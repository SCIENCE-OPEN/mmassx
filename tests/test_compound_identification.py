from pathlib import Path
from types import SimpleNamespace

import pytest

from gui import config, doc, libs
from gui.panel_compounds_search import CurrentCompound, panelCompoundsSearch
import gui.panel_compounds_search as compounds_panel
from gui.panel_match import panelMatch
import mspy


def make_ion(name, charge, adduct="[M+H]+", isotope=None):
    return CurrentCompound(
        name=name,
        mz=100.0 / abs(charge),
        z=charge,
        adduct=adduct,
        formula="C6H12O6",
        isotope=isotope,
    )


def test_current_compound_match_lists_are_independent():
    first = make_ion("first", 1)
    second = make_ion("second", 1)

    first.matches.append("match")

    assert second.matches == []


def test_cache_loads_every_requested_charge(tmp_path, monkeypatch):
    monkeypatch.setattr(compounds_panel, "ION_CACHE_DIR", tmp_path)
    for charge in (1, 2):
        compounds_panel.save_ions_to_cache(
            "glucose", "C6H12O6", "[M+H]+", charge, None, 0,
            [make_ion("glucose", charge)],
        )

    loaded = compounds_panel.load_compound_ions(
        "glucose", ["[M+H]+"], [1, 2], [], 0, "C6H12O6"
    )

    assert {ion.z for ion in loaded} == {1, 2}


def test_incomplete_cache_is_reported_as_a_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(compounds_panel, "ION_CACHE_DIR", tmp_path)
    compounds_panel.save_ions_to_cache(
        "glucose", "C6H12O6", "[M+H]+", 1, None, 0,
        [make_ion("glucose", 1)],
    )

    loaded = compounds_panel.load_compound_ions(
        "glucose", ["[M+H]+", "[M+Na]+"], [1], [], 0, "C6H12O6"
    )

    assert loaded is None


def test_invalid_base_configuration_is_a_complete_cache_result(tmp_path, monkeypatch):
    monkeypatch.setattr(compounds_panel, "ION_CACHE_DIR", tmp_path)
    compounds_panel.mark_config_invalid(
        "glucose", "C6H12O6", "[M+H]+", 1, None, 0
    )

    loaded = compounds_panel.load_compound_ions(
        "glucose", ["[M+H]+"], [1], ["(13)C1"], 0, "C6H12O6"
    )

    assert loaded == []


def test_saving_valid_ions_clears_an_invalid_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(compounds_panel, "ION_CACHE_DIR", tmp_path)
    compounds_panel.mark_config_invalid(
        "glucose", "C6H12O6", "[M+H]+", 1, None, 0
    )
    ion = make_ion("glucose", 1)

    compounds_panel.save_ions_to_cache(
        "glucose", "C6H12O6", "[M+H]+", 1, None, 0, [ion]
    )

    loaded = compounds_panel.load_compound_ions(
        "glucose", ["[M+H]+"], [1], [], 0, "C6H12O6"
    )
    assert [(item.name, item.z, item.adduct) for item in loaded] == [
        ("glucose", 1, "[M+H]+")
    ]


def test_cache_round_trips_base_and_selected_isotope(tmp_path, monkeypatch):
    monkeypatch.setattr(compounds_panel, "ION_CACHE_DIR", tmp_path)
    base = make_ion("glucose", 1)
    isotope = make_ion("glucose", 1, isotope="(13)C1")
    compounds_panel.save_ions_to_cache(
        "glucose", "C6H12O6", "[M+H]+", 1, None, 0, [base]
    )
    compounds_panel.save_ions_to_cache(
        "glucose", "C6H12O6", "[M+H]+", 1, "(13)C1", 0, [isotope]
    )

    loaded = compounds_panel.load_compound_ions(
        "glucose", ["[M+H]+"], [1], ["(13)C1"], 0, "C6H12O6"
    )

    assert {ion.isotope for ion in loaded} == {None, "(13)C1"}


def test_generation_preserves_compounds_loaded_from_cache():
    config.compoundsSearch.update(
        maxCharge=1,
        radicals=0,
        adducts=[],
        isotopes=[],
        massType=0,
        saveCache=0,
    )
    tool = SimpleNamespace(currentCompounds=[make_ion("cached", 1)])

    panelCompoundsSearch.runGenerateIons(
        tool, {"computed": mspy.obj_compound.compound("H2O")}
    )

    assert {ion.name for ion in tool.currentCompounds} == {"cached", "computed"}


def test_generation_ignores_adducts_of_the_opposite_polarity():
    config.compoundsSearch.update(
        maxCharge=1,
        radicals=0,
        adducts=["[M-H]-"],
        isotopes=[],
        massType=0,
        saveCache=0,
    )
    tool = SimpleNamespace(currentCompounds=[])

    panelCompoundsSearch.runGenerateIons(
        tool, {"glucose": mspy.obj_compound.compound("C6H12O6")}
    )

    assert {ion.adduct for ion in tool.currentCompounds} == {"[M+H]+"}


def test_generated_cache_round_trips_all_charges_and_isotopes(tmp_path, monkeypatch):
    monkeypatch.setattr(compounds_panel, "ION_CACHE_DIR", tmp_path)
    config.compoundsSearch.update(
        maxCharge=2,
        radicals=0,
        adducts=["[M+Na]+"],
        isotopes=["(13)C1", "(15)N1"],
        massType=0,
        saveCache=1,
    )
    tool = SimpleNamespace(currentCompounds=[])

    panelCompoundsSearch.runGenerateIons(
        tool, {"glycine": mspy.obj_compound.compound("C2H5NO2")}
    )
    loaded = compounds_panel.load_compound_ions(
        "glycine",
        ["[M+Na]+", "[M+H]+"],
        [1, 2],
        ["(13)C1", "(15)N1"],
        0,
        "C2H5NO2",
    )

    assert len(tool.currentCompounds) == 16
    assert len(loaded) == 16
    assert {ion.z for ion in loaded} == {1, 2}
    assert {ion.isotope for ion in loaded} == {
        None,
        "(13)C1",
        "(15)N1",
        "(13)C1(15)N1",
    }


def test_invalid_isotope_substitutions_are_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(compounds_panel, "ION_CACHE_DIR", tmp_path)
    config.compoundsSearch.update(
        maxCharge=1,
        radicals=0,
        adducts=[],
        isotopes=["(13)C1", "(15)N1"],
        massType=0,
        saveCache=1,
    )
    tool = SimpleNamespace(currentCompounds=[])

    panelCompoundsSearch.runGenerateIons(
        tool, {"glucose": mspy.obj_compound.compound("C6H12O6")}
    )
    loaded = compounds_panel.load_compound_ions(
        "glucose",
        ["[M+H]+"],
        [1],
        ["(13)C1", "(15)N1"],
        0,
        "C6H12O6",
    )

    assert loaded is not None
    assert {ion.isotope for ion in loaded} == {None, "(13)C1"}


def test_zero_maximum_charge_is_rejected():
    with pytest.raises(ValueError, match="cannot be zero"):
        compounds_panel.get_signed_charges(0)


def test_stop_uses_the_python3_thread_api(monkeypatch):
    stopped = []
    monkeypatch.setattr(mspy.mod_stopper, "stop", lambda: stopped.append(True))
    tool = SimpleNamespace(processing=SimpleNamespace(is_alive=lambda: True))

    panelCompoundsSearch.onStop(tool, None)

    assert stopped == [True]


def test_radical_ions_create_radical_annotations():
    annotation = doc.annotation(label="", mz=100.0, ai=1.0)
    compound = make_ion("radical", 1, adduct="M*")
    compound.matches = [annotation]
    document = SimpleNamespace(
        annotations=[],
        backup=lambda *_: None,
        sortAnnotations=lambda: None,
    )
    parent = SimpleNamespace(onDocumentChanged=lambda **_: None)
    tool = SimpleNamespace(
        currentDocument=document,
        currentCompounds=[compound],
        parent=parent,
    )

    panelCompoundsSearch.onAnnotate(tool, None)

    assert annotation.radical == 1
    assert annotation.label == "radical (radical)"


def test_measured_mz_belongs_to_the_best_match():
    config.match.update(units="ppm", tolerance=20, ignoreCharge=0)
    row = ["compound", 100.0, 1, "[M+H]+", "H", None, [], None, None]
    matcher = SimpleNamespace(
        currentModule="compounds",
        currentData=[row],
        currentPeaklist=[
            mspy.obj_peak.peak(100.0001, 1, charge=1),
            mspy.obj_peak.peak(100.0010, 1, charge=1),
        ],
        makeMatchSummary=lambda: None,
    )

    panelMatch.runMatch(matcher)

    assert row[5] == pytest.approx(1.0)
    assert row[7] == pytest.approx(100.0001)


def test_isotope_choices_are_saved(tmp_path):
    config.compoundsSearch["isotopes"] = ["(13)C1", "(15)N2"]
    path = tmp_path / "config.xml"

    config.saveConfig(path)

    text = path.read_text(encoding="utf-8")
    assert '<param name="isotopes" value="(13)C1;(15)N2" type="str" />' in text


def test_compound_library_skips_entries_without_a_name_or_formula(tmp_path):
    path = tmp_path / "compounds.xml"
    path.write_text(
        '<mMassCompounds><group name="test">'
        '<compound name="missing" formula="" />'
        '<compound name="" formula="H2O" />'
        '<compound name="water" formula="H2O" />'
        '</group></mMassCompounds>',
        encoding="utf-8",
    )

    original = libs.compounds.copy()
    try:
        libs.loadCompounds(str(path))
        assert set(libs.compounds["test"]) == {"water"}
    finally:
        libs.compounds.clear()
        libs.compounds.update(original)
