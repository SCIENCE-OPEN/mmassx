import importlib
import inspect
import multiprocessing
import pickle
import sys


def import_precompute(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["precompute_ions_cache.py"])
    sys.modules.pop("precompute_ions_cache", None)
    return importlib.import_module("precompute_ions_cache")


def test_isotope_definitions_are_not_treated_as_adducts(monkeypatch, tmp_path):
    module = import_precompute(monkeypatch, tmp_path)

    assert module.ADDUCTS
    assert not any(adduct.startswith("(") for adduct in module.ADDUCTS)


def test_pool_worker_is_top_level_and_picklable(monkeypatch, tmp_path):
    module = import_precompute(monkeypatch, tmp_path)

    pickle.dumps(module.generate_task)


def test_precompute_and_gui_use_the_same_cache_key(monkeypatch, tmp_path):
    module = import_precompute(monkeypatch, tmp_path)
    from gui import panel_compounds_search

    args = ("glucose", "[M+H]+", 1, "(13)C1", 0)
    assert module.config_to_hash(*args) == panel_compounds_search.config_to_hash(*args)


def test_task_generation_is_streamed(monkeypatch, tmp_path):
    module = import_precompute(monkeypatch, tmp_path)

    tasks = module.generate_tasks({}, [], 1, [], 0)

    assert inspect.isgenerator(tasks)


def test_pool_worker_generates_a_cache_file(monkeypatch, tmp_path):
    module = import_precompute(monkeypatch, tmp_path)
    output_root = tmp_path / "ions"
    task = (
        "water",
        module.Compound("H2O"),
        "[M+H]+",
        1,
        None,
        0,
    )

    context = multiprocessing.get_context("spawn")
    with context.Pool(
        1,
        initializer=module.configure_output_root,
        initargs=(str(output_root),),
    ) as pool:
        pool.apply(module.generate_task, (task,))

    hash_id = module.config_to_hash("water", "[M+H]+", 1, None, 0)
    assert (output_root / "H2O" / f"{hash_id}.joblib").exists()
