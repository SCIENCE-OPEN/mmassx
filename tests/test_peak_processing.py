import numpy
import pytest

import mspy


def make_peak(mz, intensity):
    return mspy.obj_peak.peak(float(mz), float(intensity))


def test_savgol_reuses_coefficients_for_every_point_and_cycle():
    x_values = numpy.arange(11, dtype=numpy.float64)
    signal = numpy.column_stack((x_values, x_values**2))

    smoothed = mspy.mod_signal.savgol(signal, window=5.0, cycles=2)

    assert smoothed[4:-4, 1] == pytest.approx(signal[4:-4, 1])


def test_deisotope_uses_an_integer_pattern_table_index():
    peaks = mspy.obj_peaklist.peaklist([
        make_peak(100.0, 100.0),
        make_peak(100.0 + mspy.mod_peakpicking.ISOTOPE_DISTANCE, 5.9),
    ])

    peaks.deisotope(maxCharge=1)

    assert [(peak.charge, peak.isotope) for peak in peaks] == [
        (1, 0),
        (1, 1),
    ]


def test_peaklist_supports_nested_iteration():
    peaks = mspy.obj_peaklist.peaklist([
        make_peak(100.0, 10.0),
        make_peak(200.0, 20.0),
        make_peak(300.0, 30.0),
    ])

    pairs = [(outer.mz, inner.mz) for outer in peaks for inner in peaks]

    assert len(pairs) == 9
    assert pairs[-1] == (300.0, 300.0)


def test_replacing_a_zero_intensity_peak_does_not_divide_by_zero():
    peaks = mspy.obj_peaklist.peaklist([
        make_peak(100.0, 0.0),
        make_peak(200.0, 0.0),
    ])

    peaks[1] = make_peak(200.0, 0.0)

    assert [peak.ri for peak in peaks] == [1.0, 1.0]


def test_normalizing_an_all_zero_signal_preserves_finite_values():
    signal = numpy.array([[100.0, 0.0], [101.0, 0.0]])

    normalized = mspy.mod_signal.normalize(signal)

    assert numpy.array_equal(normalized, signal)
    assert numpy.isfinite(normalized).all()


def test_scan_normalization_does_not_create_nan_for_zero_intensity():
    signal = numpy.array([[100.0, 0.0], [101.0, 0.0]])
    scan = mspy.obj_scan.scan(profile=signal.copy())

    scan.normalize()

    assert numpy.array_equal(scan.profile, signal)
    assert numpy.isfinite(scan.profile).all()
