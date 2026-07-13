# tests/test_engine.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.power_analysis import compute_sample_size
from src.engine.srm_check import detect_srm
from src.engine.ztest import run_ztest


def test_power_output_keys():
    result = compute_sample_size(p0=0.05, mde=0.02)
    assert 'n_per_group' in result
    assert 'n_total' in result
    assert result['n_total'] == result['n_per_group'] * 2
    print('test_power_output_keys: PASSED')


def test_larger_mde_requires_fewer_users():
    small = compute_sample_size(p0=0.05, mde=0.01)
    large = compute_sample_size(p0=0.05, mde=0.05)
    assert small['n_per_group'] > large['n_per_group']
    print('test_larger_mde_requires_fewer_users: PASSED')


def test_srm_clean_split_passes():
    result = detect_srm(5000, 5000)
    assert result['srm_detected'] is False
    assert result['verdict'] == 'PASS'
    print('test_srm_clean_split_passes: PASSED')


def test_srm_imbalanced_split_detected():
    result = detect_srm(3000, 7000)
    assert result['srm_detected'] is True
    print('test_srm_imbalanced_split_detected: PASSED')


def test_ztest_significant_positive():
    result = run_ztest(n_c=10000, x_c=500, n_t=10000, x_t=650)
    assert result['significant'] is True
    assert result['absolute_lift'] > 0
    assert result['ci_95'][0] > 0
    print('test_ztest_significant_positive: PASSED')


def test_ztest_insignificant_small_sample():
    result = run_ztest(n_c=100, x_c=5, n_t=100, x_t=6)
    assert result['significant'] is False
    print('test_ztest_insignificant_small_sample: PASSED')


def test_ztest_ci_excludes_zero_when_significant():
    result = run_ztest(n_c=10000, x_c=500, n_t=10000, x_t=650)
    assert result['ci_95'][0] > 0
    print('test_ztest_ci_excludes_zero_when_significant: PASSED')


if __name__ == '__main__':
    test_power_output_keys()
    test_larger_mde_requires_fewer_users()
    test_srm_clean_split_passes()
    test_srm_imbalanced_split_detected()
    test_ztest_significant_positive()
    test_ztest_insignificant_small_sample()
    test_ztest_ci_excludes_zero_when_significant()
    print('\nAll 7 tests passed.')