import os
import sys
import joblib
import hashlib
import argparse
from time import time
from pathlib import Path
from xml.dom.minidom import parse
from multiprocessing import Pool, cpu_count, Value, Lock
from mspy.obj_compound import compound as Compound
from gui.panel_compounds_search import FORMULAS, CurrentCompound
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- Configuration ----------
COMPOUND_XML = os.path.join("configs", "compounds.xml")
MASS_TYPE = 0  # 0 = monoisotopic, 1 = average
MAX_CHARGE = 1
RADICALS = True
ADDUCTS = list(FORMULAS.keys())
ISOTOPES = [iso for iso in FORMULAS if iso.startswith("(")]

# ---------- Argument parsing ----------
parser = argparse.ArgumentParser(description="Precompute ion configurations for compounds.")
parser.add_argument('--home', action='store_true', help="Use ~/.mmass/cache as output directory")
parser.add_argument('--group-name', type=str, default=None, help="Optional: limit to a specific group name in compounds.xml")
args = parser.parse_args()

# ---------- Output directory ----------
OUTPUT_ROOT = Path.home() / '.mmass' / 'cache' / 'ions' if args.home else Path("cache/ions")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# ---------- Utility Functions ----------
def config_to_hash(name: str, adduct: str, charge: int, isotope: str, mass_type: int) -> str:
    key = f"{name}|{adduct}|{charge}|{isotope or ''}|{mass_type}"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    log_path = OUTPUT_ROOT / 'config_hash_log.txt'
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"{h} | {key}\n")
    except Exception as e:
        print(f"[config_to_hash] Failed to write log: {e}")
    return h

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
                return
        else:
            mz = c.mz(charge)[mass_type]
            result.append(CurrentCompound(name=name, mz=mz, z=charge, adduct=adduct, formula=c.expression))

    except Exception as e:
        print(f"[{name}] Error generating ion for {adduct}, {isotope}: {e}")
        out_dir.mkdir(parents=True, exist_ok=True)
        invalid_path.touch()
        return

    if result:
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            joblib.dump(result, out_path, compress=("zlib", 3))
        except Exception as e:
            print(f"[{name}] Failed to save ions: {e}")
            invalid_path.touch()

def check_and_prepare_task(name, cmpd, adduct, charge, isotope, mass_type):
    hash_id = config_to_hash(name, adduct, charge, isotope, mass_type)
    out_dir = OUTPUT_ROOT / cmpd.expression
    out_path = out_dir / (hash_id + ".joblib")
    invalid_path = out_dir / (hash_id + ".invalid")

    if not out_path.exists() and not invalid_path.exists():
        return (name, cmpd, adduct, charge, isotope, mass_type)
    return None

def generate_tasks(compounds, adducts, charge, isotopes, mass_type, max_threads=32):
    tasks, futures = [], []
    total_compounds = len(compounds)
    total_possible = total_compounds * len(adducts) * (len(isotopes) + 1)
    print(f"Scanning approximately {total_possible} configs...")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for name, cmpd in compounds.items():
            for adduct in adducts:
                for iso in isotopes:
                    futures.append(executor.submit(check_and_prepare_task, name, cmpd, adduct, charge, iso, mass_type))
                futures.append(executor.submit(check_and_prepare_task, name, cmpd, adduct, charge, None, mass_type))

        total_scanned = len(futures)
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                tasks.append(result)
            if i % 1000 == 0 or i == total_scanned:
                print(f"Checked {i}/{total_scanned} configs. New tasks: {len(tasks)}", end='\r')

    already_existing = total_possible - len(tasks)
    print(f"\nSummary for charge {charge}:")
    print(f"  Total configs:         {total_possible}")
    print(f"  Already cached:        {already_existing}")
    print(f"  New to generate:       {len(tasks)}")

    return tasks

# ---------- Main ----------
if __name__ == "__main__":
    print("Reading compounds from XML...")
    compounds = get_all_compounds(COMPOUND_XML, args.group_name)
    if not compounds:
        sys.exit(1)

    mass_type = MASS_TYPE
    adducts = ADDUCTS
    isotopes = ISOTOPES
    workers = get_safe_cpu_count(reserve=2)
    print(f"Using {workers} worker(s)\n")

    for polarity in [+1, -1]:
        charge = polarity
        tasks = generate_tasks(compounds, adducts, charge, isotopes, mass_type)
        total_tasks = len(tasks)

        if total_tasks == 0:
            print(f"No new tasks for charge {charge}")
            continue

        print(f"Generating {total_tasks} ion configs for charge {charge}...")
        counter = Value('i', 0)
        lock = Lock()

        def wrapped_generate(*args):
            with lock:
                counter.value += 1
                print(f"Progress [{charge:+}]: {counter.value}/{total_tasks}", end='\r')
            return generate_single_config_ions(*args)

        with Pool(processes=workers) as pool:
            pool.starmap(wrapped_generate, tasks)

        print(f"\nDone: {counter.value}/{total_tasks} generated for charge {charge}")

    print("\nAll done! Ion cache stored in:", OUTPUT_ROOT)
