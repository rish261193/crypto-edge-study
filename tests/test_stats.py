import numpy as np
import pandas as pd
import pytest

from study import stats as S

UTC = "UTC"


def trade(pair="BTC/USD", open_date="2020-01-02", close_date="2020-01-04 12:00",
          amount=1.0, open_rate=100.0, close_rate=110.0, fee=0.01, stop=95.0):
    gross = amount * (close_rate - open_rate)
    fees = amount * open_rate * fee + amount * close_rate * fee
    return {"pair": pair, "open_date": pd.Timestamp(open_date, tz=UTC),
            "close_date": pd.Timestamp(close_date, tz=UTC), "amount": amount,
            "open_rate": open_rate, "close_rate": close_rate, "fee_open": fee,
            "fee_close": fee, "profit_abs": gross - fees, "stop_loss_abs": stop}


def closes(values, start="2020-01-01", pair="BTC/USD"):
    idx = pd.date_range(start, periods=len(values), freq="1D", tz=UTC)
    return pd.DataFrame({pair: values}, index=idx)


def test_daily_equity_marks_open_trade_and_books_realised_profit():
    c = closes([100, 100, 104, 108, 112, 112])
    t = pd.DataFrame([trade()])
    eq = S.daily_equity(t, c, 500.0, c.index)
    # day 0: flat; day 1 (opened at 00:00): marked at 100 less entry fee 1.0
    assert eq.iloc[0] == 500.0
    assert eq.iloc[1] == pytest.approx(499.0)
    assert eq.iloc[2] == pytest.approx(500 + 4 - 1.0)
    # closes during day 3 (2020-01-04 12:00): realised from the end of that day
    assert eq.iloc[3] == pytest.approx(500 + t["profit_abs"].iloc[0])
    assert t["profit_abs"].iloc[0] == pytest.approx(7.9)
    assert eq.iloc[-1] == pytest.approx(500 + t["profit_abs"].sum())


def test_exposure_is_position_value_over_equity():
    c = closes([100, 100, 104, 108, 112, 112])
    t = pd.DataFrame([trade()])
    eq = S.daily_equity(t, c, 500.0, c.index)
    ex = S.daily_exposure(t, c, eq)
    assert ex.iloc[0, 0] == 0
    assert ex.iloc[2, 0] == pytest.approx(104 / eq.iloc[2])
    assert ex.iloc[4, 0] == 0


def test_block_bootstrap_is_seeded_and_centred():
    x = np.random.default_rng(1).normal(0.001, 0.02, 2000)
    a = S.circular_block_means(x, len(x), 2000, 20, np.random.default_rng(5))
    b = S.circular_block_means(x, len(x), 2000, 20, np.random.default_rng(5))
    assert np.array_equal(a, b)
    assert abs(a.mean() - x.mean()) < 2e-4


def test_lower_bound_of_constant_series_is_the_constant():
    x = np.full(100, 0.002)
    assert S.lower_bound(x, np.random.default_rng(0), n=200) == pytest.approx(0.002)


def test_lower_bound_coverage_is_roughly_95_percent():
    rng = np.random.default_rng(11)
    hits = 0
    for _ in range(200):
        x = rng.normal(0.0, 0.02, 400)
        hits += S.lower_bound(x, rng, n=500) <= 0.0
    assert 0.88 <= hits / 200 <= 0.995


def test_timing_skill_beats_shifted_nulls_and_noise_does_not():
    rng = np.random.default_rng(3)
    n = 1500
    idx = pd.date_range("2018-01-01", periods=n, freq="1D", tz=UTC)
    r = pd.DataFrame({"A": rng.normal(0, 0.03, n)}, index=idx)
    shifts = S.draw_shifts(n, rng, n=300)
    # perfect foresight: hold exactly on up days (exposure set the day before)
    skilled = pd.DataFrame({"A": (r["A"].shift(-1) > 0).astype(float).fillna(0)}, index=idx)
    real = S.exposure_model_returns(skilled, r, 0.0).mean()
    assert np.mean(S.null_means(skilled, r, 0.0, shifts) < real) > 0.99
    noise = pd.DataFrame({"A": (rng.random(n) > 0.5).astype(float)}, index=idx)
    real_noise = S.exposure_model_returns(noise, r, 0.0).mean()
    pct = np.mean(S.null_means(noise, r, 0.0, shifts) < real_noise)
    assert 0.02 < pct < 0.98


def test_fee_is_charged_on_turnover():
    idx = pd.date_range("2020-01-01", periods=3, freq="1D", tz=UTC)
    r = pd.DataFrame({"A": [0.0, 0.0, 0.0]}, index=idx)
    e = pd.DataFrame({"A": [0.0, 0.5, 0.0]}, index=idx)
    out = S.exposure_model_returns(e, r, 0.01)
    assert out.tolist() == pytest.approx([0.0, -0.005, -0.005])


@pytest.mark.parametrize("mean,pct,trades,expected", [
    (0.003, 0.99, 120, "PASS_INSAMPLE"),
    (0.003, 0.80, 120, "INCONCLUSIVE"),
    (0.003, 0.99, 20, "INCONCLUSIVE"),
    (-0.001, 0.99, 120, "FAIL"),
    (0.003, 0.30, 120, "FAIL"),
])
def test_in_sample_verdict_rules(mean, pct, trades, expected):
    rng = np.random.default_rng(0)
    r = rng.normal(mean, 0.001 if mean > 0 else 0.02, 2000)
    nulls = np.linspace(-1, 1, 1000)
    model_mean = float(np.quantile(nulls, pct))
    res = S.in_sample_verdict(r, trades, model_mean + 1e-12, nulls, rng)
    assert res.verdict == expected


def test_final_verdict_requires_holdout_only_for_passes():
    assert S.final_verdict("FAIL", None, None) == "FAIL"
    assert S.final_verdict("INCONCLUSIVE", None, None) == "INCONCLUSIVE"
    assert S.final_verdict("PASS_INSAMPLE", 0.001, 0.0) == "PASS"
    assert S.final_verdict("PASS_INSAMPLE", -0.002, -0.001) == "FAIL"
    with pytest.raises(ValueError):
        S.final_verdict("PASS_INSAMPLE", None, None)


def test_r_multiples_use_planned_risk():
    t = pd.DataFrame([trade(open_rate=100, close_rate=90, stop=95, fee=0.0)])
    assert S.r_multiples(t).iloc[0] == pytest.approx(-2.0)


def test_reality_check_uses_the_best_configuration():
    p = S.reality_check_pvalue({"a": 0.5, "b": 0.1},
                               {"a": np.array([0.0, 0.6, 0.2]), "b": np.array([0.7, 0.0, 0.1])})
    assert p == pytest.approx(2 / 3)
