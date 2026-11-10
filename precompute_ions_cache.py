import os
import sys
import joblib
import hashlib
import argparse
from pathlib import Path
from xml.dom.minidom import parse
from multiprocessing import Pool, cpu_count
from mspy.obj_compound import compound as Compound
from gui.panel_compounds_search import FORMULAS, CurrentCompound

# ---------- Configuration ----------
COMPOUND_XML = os.path.join("configs", "compounds.xml")
MASS_TYPE = 0  # 0 = monoisotopic, 1 = average
ADDUCTS = [name for name in FORMULAS if not name.startswith('(')]
ISOTOPES = [iso for iso in FORMULAS if iso.startswith("(")]
CACHE_VERSION = 2

# ---------- Output directory ----------
OUTPUT_ROOT = Path("cache/ions")

# ---------- Utility Functions ----------
def config_to_hash(name: str, adduct: str, charge: int, isotope: str, mass_type: int) -> str:
    key = f"{CACHE_VERSION}|{name}|{adduct}|{charge}|{isotope or ''}|{mass_type}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]

def configure_output_root(path):
    """Set the output root in the parent process and spawned workers."""
    global OUTPUT_ROOT
    OUTPUT_ROOT = Path(path)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

def build_parser():
    parser = argparse.ArgumentParser(description="Precompute ion configurations for compounds.")
    parser.add_argument('--home', action='store_true', help="Use ~/.mmass/cache as output directory")
    parser.add_argument('--group-name', type=str, default=None, help="Optional: limit to a specific group name in compounds.xml")
    return parser

def get_safe_cpu_count(reserve=2):
    return max(1, (cpu_count() or 1) - reserve)

def get_all_compounds(xml_path, group_name=None):
    compounds = {}
    doc = parse(xml_path)
    groups = doc.getElementsByTagName("group")

    selected_groups = [g for g in groups if g.getAttribute("name") == group_name] if group_name else groups
    if not selected_groups:
        print(f"No group found with name '{group_name}'")
        return {}

    for group in selected_groups:
        for ctag in group.getElementsByTagName("compound"):
            name = ctag.getAttribute("name")
            formula = ctag.getAttribute("formula")
            if not name or not formula:
                continue
            try:
                c = Compound(formula)
                compounds[name] = c
            except Exception:
                continue
    print(f"Loaded {len(compounds)} compounds.")
    return compounds

def generate_single_config_ions(name, compound, adduct, charge, isotope, mass_type):
    result = []
    hash_id = config_to_hash(name, adduct, charge, isotope, mass_type)
    out_dir = OUTPUT_ROOT / compound.expression
    out_path = out_dir / (hash_id + ".joblib")
    invalid_path = out_dir / (hash_id + ".invalid")

    try:
        adduct_formula = FORMULAS[adduct]
        if adduct in ('[M+Li]+', '[M+Na-2H]-', '[M+K-2H]-', '[M+Na]+', '[M+K]+', '[M+NH4]+'):
            formula = f'{compound.expression}({adduct_formula})(H-1)'
        elif adduct in ('[M+Cl]-', '[M-CH3]-', '[M-C3H10N]-', '[M-C5H12N]-'):
            formula = f'{compound.expression}({adduct_formula})(H)'
        elif adduct in ('[2M+Na]+', '[2M+K]+', '[2M+NH4]+', '[2M+H]+', '[2M-H]-'):
            formula = f'{2 * compound.expression}({adduct_formula})(H-1)'
        elif adduct in ('[2M+Cl]-', '[2M+Na-2H]-', '[2M+K-2H]-'):
            formula = f'{2 * compound.expression}({adduct_formula})(H)'
        elif adduct in ('[M-H2O-H]-', '[M-H2O+H]+', '[+MeOH+H]+', '[+ACN+H]+',
                        '[M+FMP10]+', '[M+2FMP10]+', '[M+2FMP10-CH3]+',
                        '[M+AMPP]+', '[M+2AMPP]+', '[M+3AMPP]+'):
            formula = f'{compound.expression}({adduct_formula})'
        else:
            formula = compound.expression

        c = Compound(formula)
        if not c.isvalid():
            out_dir.mkdir(parents=True, exist_ok=True)
            invalid_path.touch()
            out_path.unlink(missing_ok=True)
            return

        if isotope:
            iso_formula = f'{formula}({FORMULAS[isotope]})'
            ci = Compound(iso_formula)
            if ci.isvalid():
                mz = ci.mz(charge)[mass_type]
                result.append(CurrentCompound(name=name, mz=mz, z=charge, adduct=adduct,
                                              isotope=isotope, formula=ci.expression))
            else:
                out_dir.mkdir(parents=True, exist_ok=True)
                invalid_path.touch()
                out_path.unlink(missing_ok=True)
                return
        else:
            mz = c.mz(charge)[mass_type]
            result.append(CurrentCompound(name=name, mz=mz, z=charge, adduct=adduct, formula=c.expression))

    except Exception as e:
        print(f"[{name}] Error generating ion for {adduct}, {isotope}: {e}")
        out_dir.mkdir(parents=True, exist_ok=True)
        invalid_path.touch()
        out_path.unlink(missing_ok=True)
        return

    if result:
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            joblib.dump(result, out_path, compress=("zlib", 3))
            invalid_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"[{name}] Failed to save ions: {e}")
            invalid_path.touch()
            out_path.unlink(missing_ok=True)

def check_and_prepare_task(name, cmpd, adduct, charge, isotope, mass_type):
    hash_id = config_to_hash(name, adduct, charge, isotope, mass_type)
    out_dir = OUTPUT_ROOT / cmpd.expression
    out_path = out_dir / (hash_id + ".joblib")
    invalid_path = out_dir / (hash_id + ".invalid")

    if not out_path.exists() and not invalid_path.exists():
        return (name, cmpd, adduct, charge, isotope, mass_type)
    return None

def generate_tasks(compounds, adducts, charge, isotopes, mass_type):
    """Yield uncached configurations without retaining millions of futures."""
    for name, cmpd in compounds.items():
        for adduct in adducts:
            for isotope in list(isotopes) + [None]:
                task = check_and_prepare_task(
                    name, cmpd, adduct, charge, isotope, mass_type
                )
                if task:
                    yield task

def generate_task(args):
    """Picklable multiprocessing entry point for one ion configuration."""
    return generate_single_config_ions(*args)

# ---------- Main ----------
def main(argv=None):
    args = build_parser().parse_args(argv)
    output_root = Path.home() / '.mmass' / 'cache' / 'ions' if args.home else Path("cache/ions")
    configure_output_root(output_root)

    print("Reading compounds from XML...")
    compounds = get_all_compounds(COMPOUND_XML, args.group_name)
    if not compounds:
        sys.exit(1)

    mass_type = MASS_TYPE
    isotopes = ISOTOPES
    workers = get_safe_cpu_count(reserve=2)
    print(f"Using {workers} worker(s)\n")

    for polarity in [+1, -1]:
        charge = polarity
        suffix = '+' if polarity > 0 else '-'
        adducts = [adduct for adduct in ADDUCTS if adduct.endswith(suffix)]
        tasks = generate_tasks(compounds, adducts, charge, isotopes, mass_type)
        print(f"Generating missing ion configs for charge {charge}...")
        completed = 0
        with Pool(
            processes=workers,
            initializer=configure_output_root,
            initargs=(str(OUTPUT_ROOT),),
        ) as pool:
            for completed, _ in enumerate(
                pool.imap_unordered(generate_task, tasks, chunksize=20), 1
            ):
                if completed % 1000 == 0:
                    print(f"Progress [{charge:+}]: {completed}", end='\r')

        print(f"\nDone: {completed} generated for charge {charge}")

    print("\nAll done! Ion cache stored in:", OUTPUT_ROOT)

if __name__ == "__main__":
    main()
