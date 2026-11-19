from types import SimpleNamespace

import pytest

from gui import config
from gui.panel_mass_calculator import panelMassCalculator
import gui.panel_mass_calculator as mass_calculator_panel
import mspy


class ValueControl:
    def __init__(self, value):
        self.value = value

    def GetValue(self):
        return self.value

    def ChangeValue(self, value):
        self.value = value


def make_mass_calculator(agent_charge):
    return SimpleNamespace(
        compound_value=ValueControl('H2O'),
        ionseriesAgentFormula_value=ValueControl('H'),
        ionseriesAgentCharge_value=ValueControl(str(agent_charge)),
        ionseriesNegative_radio=ValueControl(False),
        patternFwhm_value=ValueControl('0.1'),
        patternIntensity_value=ValueControl('100'),
        patternBaseline_value=ValueControl('0'),
        patternShift_value=ValueControl('0'),
        showPeaks_check=ValueControl(True),
        patternPeakShape_choice=SimpleNamespace(
            GetStringSelection=lambda: 'Gaussian'
        ),
        currentCompound=None,
    )


def test_water_reference_masses_are_unchanged():
    water = mspy.obj_compound.compound('H2O')

    assert water.mass(0) == pytest.approx(18.0105646863)
    assert water.mass(1) == pytest.approx(18.0152864362)


@pytest.mark.parametrize('charge', [-3, -1, 1, 3])
def test_mz_round_trip_recovers_neutral_mass(charge):
    neutral_mass = (500.123456, 500.5)

    ion_mass = mspy.mod_basics.mz(neutral_mass, charge)

    assert mspy.mod_basics.mz(
        ion_mass, 0, currentCharge=charge
    ) == pytest.approx(neutral_mass)


def test_mz_supports_a_multicharged_carrier_for_compatible_charge():
    neutral_mass = 500.123456

    ion_mass = mspy.mod_basics.mz(
        neutral_mass, charge=2, agentFormula='Ca', agentCharge=2
    )

    assert mspy.mod_basics.mz(
        ion_mass,
        charge=0,
        currentCharge=2,
        agentFormula='Ca',
        agentCharge=2,
    ) == pytest.approx(neutral_mass)


def test_mz_rejects_a_zero_charge_carrier():
    with pytest.raises(ValueError, match='charge'):
        mspy.mod_basics.mz(500.0, charge=1, agentCharge=0)


def test_mz_rejects_fractional_charge_carriers():
    with pytest.raises(ValueError, match='multiple'):
        mspy.mod_basics.mz(
            500.0, charge=1, agentFormula='Ca', agentCharge=2
        )


def test_compound_is_invalid_with_fractional_charge_carriers():
    compound = mspy.obj_compound.compound('H2O')

    assert not compound.isvalid(
        charge=1, agentFormula='Ca', agentCharge=2
    )


def test_pattern_rejects_fractional_charge_carriers():
    compound = mspy.obj_compound.compound('H2O')

    with pytest.raises(ValueError, match='multiple'):
        compound.pattern(
            charge=1,
            agentFormula='Ca',
            agentCharge=2,
            real=False,
        )


def test_sequence_composition_removes_zero_count_atoms():
    sequence = mspy.obj_sequence.sequence('G')
    sequence.reset()
    sequence.fragmentLosses = ['O2']

    assert sequence.composition() == {'C': 2, 'H': 5, 'N': 1}


def test_mass_calculator_rejects_a_zero_charge_carrier(monkeypatch):
    calculator = make_mass_calculator(agent_charge=0)
    monkeypatch.setattr(mass_calculator_panel.wx, 'Bell', lambda: None)

    assert not panelMassCalculator.getParams(calculator)
    assert config.massCalculator['ionseriesAgentCharge'] != 0
