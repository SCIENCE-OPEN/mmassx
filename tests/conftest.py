from copy import deepcopy

import pytest

from gui import config
import mspy


@pytest.fixture(autouse=True)
def restore_global_configuration():
    compounds_search = deepcopy(config.compoundsSearch)
    match = deepcopy(config.match)
    mass_calculator = deepcopy(config.massCalculator)
    yield
    config.compoundsSearch.clear()
    config.compoundsSearch.update(compounds_search)
    config.match.clear()
    config.match.update(match)
    config.massCalculator.clear()
    config.massCalculator.update(mass_calculator)
    mspy.mod_stopper.start()
