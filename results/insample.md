# In-sample results

Evaluation window: 2016-03-26 to 2025-11-20 (the sealed final year is not included).

Verdicts come only from the **primary universe (BTC/USD, ETH/USD) at base fees**. Other rows are supporting evidence.

## primary universe, base fees

Reality-check p-value (family-wise, not a gate): 0.055. Equal-weight buy-and-hold: mean daily +0.249%, Sharpe 1.21.

| Config | Trades | Mean daily | 95% lower bound | Sharpe | Beats nulls | Mean R/trade | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MeanReversion-threshold10-1d | 179 | -0.004% | -0.007% | -0.69 | 29% | -0.09R | FAIL |
| MeanReversion-threshold10-4h | 895 | -0.091% | -0.103% | -5.09 | 70% | -0.36R | FAIL |
| MeanReversion-threshold20-1d | 337 | -0.009% | -0.013% | -1.16 | 22% | -0.10R | FAIL |
| MeanReversion-threshold20-4h | 1105 | -0.113% | -0.131% | -5.88 | 38% | -0.36R | FAIL |
| MeanReversion-threshold5-1d | 86 | -0.001% | -0.003% | -0.31 | 72% | -0.05R | FAIL |
| MeanReversion-threshold5-4h | 498 | -0.050% | -0.058% | -3.84 | 74% | -0.35R | FAIL |
| TrendDonchian-n100-1d | 26 | +0.049% | +0.001% | 0.58 | 92% | +6.09R | INCONCLUSIVE |
| TrendDonchian-n100-4h | 138 | +0.078% | +0.042% | 1.25 | 100% | +2.34R | PASS_INSAMPLE |
| TrendDonchian-n20-1d | 90 | +0.048% | -0.001% | 0.60 | 100% | +1.26R | INCONCLUSIVE |
| TrendDonchian-n20-4h | 558 | +0.045% | +0.010% | 0.85 | 99% | +0.32R | PASS_INSAMPLE |
| TrendDonchian-n55-1d | 42 | +0.036% | -0.007% | 0.47 | 97% | +1.96R | INCONCLUSIVE |
| TrendDonchian-n55-4h | 266 | +0.050% | +0.016% | 0.90 | 99% | +0.72R | PASS_INSAMPLE |
| VolBreakout-m1-1d | 275 | +0.020% | +0.006% | 0.88 | 100% | +0.27R | PASS_INSAMPLE |
| VolBreakout-m1-4h | 1303 | -0.100% | -0.126% | -2.05 | 63% | -0.28R | FAIL |
| VolBreakout-m1.5-1d | 138 | +0.010% | +0.001% | 0.60 | 95% | +0.27R | PASS_INSAMPLE |
| VolBreakout-m1.5-4h | 740 | -0.039% | -0.059% | -0.96 | 77% | -0.19R | FAIL |
| VolBreakout-m2-1d | 73 | +0.011% | +0.004% | 0.82 | 100% | +0.53R | PASS_INSAMPLE |
| VolBreakout-m2-4h | 400 | -0.021% | -0.037% | -0.69 | 85% | -0.18R | FAIL |

## primary universe, optimistic fees

Reality-check p-value (family-wise, not a gate): 0.048. Equal-weight buy-and-hold: mean daily +0.249%, Sharpe 1.21.

| Config | Trades | Mean daily | 95% lower bound | Sharpe | Beats nulls | Mean R/trade | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MeanReversion-threshold10-1d | 179 | -0.003% | -0.006% | -0.49 | 29% | -0.06R | FAIL |
| MeanReversion-threshold10-4h | 966 | -0.076% | -0.087% | -4.52 | 62% | -0.28R | FAIL |
| MeanReversion-threshold20-1d | 337 | -0.007% | -0.010% | -0.83 | 22% | -0.07R | FAIL |
| MeanReversion-threshold20-4h | 1344 | -0.103% | -0.118% | -5.46 | 32% | -0.27R | FAIL |
| MeanReversion-threshold5-1d | 86 | -0.001% | -0.002% | -0.16 | 72% | -0.03R | FAIL |
| MeanReversion-threshold5-4h | 498 | -0.039% | -0.046% | -3.26 | 74% | -0.28R | FAIL |
| TrendDonchian-n100-1d | 26 | +0.049% | +0.003% | 0.58 | 92% | +6.14R | INCONCLUSIVE |
| TrendDonchian-n100-4h | 138 | +0.082% | +0.046% | 1.31 | 100% | +2.44R | PASS_INSAMPLE |
| TrendDonchian-n20-1d | 90 | +0.049% | +0.001% | 0.61 | 100% | +1.29R | PASS_INSAMPLE |
| TrendDonchian-n20-4h | 558 | +0.058% | +0.024% | 1.11 | 99% | +0.40R | PASS_INSAMPLE |
| TrendDonchian-n55-1d | 42 | +0.037% | -0.008% | 0.48 | 97% | +2.00R | INCONCLUSIVE |
| TrendDonchian-n55-4h | 266 | +0.057% | +0.023% | 1.03 | 99% | +0.81R | PASS_INSAMPLE |
| VolBreakout-m1-1d | 275 | +0.024% | +0.010% | 1.04 | 100% | +0.31R | PASS_INSAMPLE |
| VolBreakout-m1-4h | 1480 | -0.073% | -0.101% | -1.47 | 53% | -0.18R | FAIL |
| VolBreakout-m1.5-1d | 138 | +0.012% | +0.003% | 0.72 | 95% | +0.31R | PASS_INSAMPLE |
| VolBreakout-m1.5-4h | 740 | -0.013% | -0.033% | -0.32 | 77% | -0.06R | FAIL |
| VolBreakout-m2-1d | 73 | +0.012% | +0.005% | 0.91 | 100% | +0.58R | PASS_INSAMPLE |
| VolBreakout-m2-4h | 400 | -0.006% | -0.021% | -0.20 | 85% | -0.05R | FAIL |

## primary universe, gross fees

Reality-check p-value (family-wise, not a gate): 0.033. Equal-weight buy-and-hold: mean daily +0.249%, Sharpe 1.21.

| Config | Trades | Mean daily | 95% lower bound | Sharpe | Beats nulls | Mean R/trade | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MeanReversion-threshold10-1d | 179 | +0.001% | -0.001% | 0.22 | 29% | +0.03R | FAIL |
| MeanReversion-threshold10-4h | 1019 | -0.005% | -0.013% | -0.34 | 63% | -0.02R | FAIL |
| MeanReversion-threshold20-1d | 337 | +0.002% | -0.002% | 0.28 | 22% | +0.02R | FAIL |
| MeanReversion-threshold20-4h | 1802 | -0.001% | -0.011% | -0.04 | 49% | -0.00R | FAIL |
| MeanReversion-threshold5-1d | 86 | +0.001% | -0.000% | 0.35 | 72% | +0.06R | INCONCLUSIVE |
| MeanReversion-threshold5-4h | 498 | -0.004% | -0.009% | -0.44 | 74% | -0.03R | FAIL |
| TrendDonchian-n100-1d | 26 | +0.050% | +0.002% | 0.59 | 92% | +6.30R | INCONCLUSIVE |
| TrendDonchian-n100-4h | 138 | +0.094% | +0.058% | 1.52 | 100% | +2.77R | PASS_INSAMPLE |
| TrendDonchian-n20-1d | 90 | +0.051% | +0.004% | 0.64 | 100% | +1.41R | PASS_INSAMPLE |
| TrendDonchian-n20-4h | 558 | +0.101% | +0.067% | 1.97 | 99% | +0.68R | PASS_INSAMPLE |
| TrendDonchian-n55-1d | 42 | +0.038% | -0.006% | 0.50 | 97% | +2.12R | INCONCLUSIVE |
| TrendDonchian-n55-4h | 266 | +0.078% | +0.044% | 1.45 | 99% | +1.10R | PASS_INSAMPLE |
| VolBreakout-m1-1d | 275 | +0.035% | +0.021% | 1.56 | 100% | +0.46R | PASS_INSAMPLE |
| VolBreakout-m1-4h | 1493 | +0.084% | +0.058% | 1.72 | 52% | +0.20R | INCONCLUSIVE |
| VolBreakout-m1.5-1d | 138 | +0.018% | +0.009% | 1.11 | 95% | +0.48R | PASS_INSAMPLE |
| VolBreakout-m1.5-4h | 741 | +0.071% | +0.051% | 1.81 | 76% | +0.35R | INCONCLUSIVE |
| VolBreakout-m2-1d | 73 | +0.015% | +0.008% | 1.18 | 100% | +0.75R | PASS_INSAMPLE |
| VolBreakout-m2-4h | 401 | +0.042% | +0.027% | 1.46 | 85% | +0.39R | INCONCLUSIVE |

## support universe, base fees

Reality-check p-value (family-wise, not a gate): 0.047. Equal-weight buy-and-hold: mean daily +0.268%, Sharpe 0.95.

| Config | Trades | Mean daily | 95% lower bound | Sharpe | Beats nulls | Mean R/trade | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MeanReversion-threshold10-1d | 180 | -0.006% | -0.009% | -0.93 | 44% | -0.11R | FAIL |
| MeanReversion-threshold10-4h | 1059 | -0.067% | -0.078% | -4.21 | 70% | -0.21R | FAIL |
| MeanReversion-threshold20-1d | 338 | -0.007% | -0.012% | -0.88 | 14% | -0.07R | FAIL |
| MeanReversion-threshold20-4h | 1376 | -0.091% | -0.107% | -4.63 | 98% | -0.22R | FAIL |
| MeanReversion-threshold5-1d | 92 | -0.002% | -0.004% | -0.42 | 86% | -0.07R | FAIL |
| MeanReversion-threshold5-4h | 648 | -0.040% | -0.048% | -3.13 | 71% | -0.21R | FAIL |
| TrendDonchian-n100-1d | 40 | +0.021% | -0.009% | 0.38 | 84% | +1.59R | INCONCLUSIVE |
| TrendDonchian-n100-4h | 281 | +0.052% | -0.001% | 0.66 | 100% | +0.76R | INCONCLUSIVE |
| TrendDonchian-n20-1d | 151 | +0.026% | +0.000% | 0.62 | 99% | +0.63R | PASS_INSAMPLE |
| TrendDonchian-n20-4h | 999 | +0.003% | -0.041% | 0.04 | 97% | -0.00R | INCONCLUSIVE |
| TrendDonchian-n55-1d | 71 | +0.022% | -0.010% | 0.40 | 84% | +0.92R | INCONCLUSIVE |
| TrendDonchian-n55-4h | 456 | +0.037% | -0.013% | 0.48 | 99% | +0.35R | INCONCLUSIVE |
| VolBreakout-m1-1d | 352 | +0.011% | -0.010% | 0.35 | 100% | +0.12R | INCONCLUSIVE |
| VolBreakout-m1-4h | 1426 | -0.094% | -0.121% | -1.88 | 96% | -0.23R | FAIL |
| VolBreakout-m1.5-1d | 161 | +0.014% | -0.003% | 0.53 | 100% | +0.31R | INCONCLUSIVE |
| VolBreakout-m1.5-4h | 1011 | -0.054% | -0.078% | -1.21 | 99% | -0.18R | FAIL |
| VolBreakout-m2-1d | 85 | +0.003% | -0.007% | 0.17 | 99% | +0.13R | INCONCLUSIVE |
| VolBreakout-m2-4h | 504 | -0.012% | -0.029% | -0.36 | 99% | -0.08R | FAIL |

## support universe, optimistic fees

Reality-check p-value (family-wise, not a gate): 0.034. Equal-weight buy-and-hold: mean daily +0.268%, Sharpe 0.95.

| Config | Trades | Mean daily | 95% lower bound | Sharpe | Beats nulls | Mean R/trade | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MeanReversion-threshold10-1d | 181 | -0.005% | -0.008% | -0.77 | 45% | -0.09R | FAIL |
| MeanReversion-threshold10-4h | 1179 | -0.057% | -0.068% | -3.57 | 68% | -0.16R | FAIL |
| MeanReversion-threshold20-1d | 342 | -0.005% | -0.010% | -0.66 | 23% | -0.05R | FAIL |
| MeanReversion-threshold20-4h | 1613 | -0.084% | -0.099% | -4.22 | 95% | -0.18R | FAIL |
| MeanReversion-threshold5-1d | 92 | -0.001% | -0.003% | -0.31 | 86% | -0.05R | FAIL |
| MeanReversion-threshold5-4h | 672 | -0.030% | -0.038% | -2.47 | 73% | -0.15R | FAIL |
| TrendDonchian-n100-1d | 40 | +0.021% | -0.009% | 0.39 | 84% | +1.62R | INCONCLUSIVE |
| TrendDonchian-n100-4h | 282 | +0.059% | +0.005% | 0.74 | 100% | +0.84R | PASS_INSAMPLE |
| TrendDonchian-n20-1d | 151 | +0.027% | +0.001% | 0.64 | 99% | +0.65R | PASS_INSAMPLE |
| TrendDonchian-n20-4h | 1008 | +0.018% | -0.025% | 0.23 | 97% | +0.06R | INCONCLUSIVE |
| TrendDonchian-n55-1d | 71 | +0.022% | -0.009% | 0.41 | 84% | +0.95R | INCONCLUSIVE |
| TrendDonchian-n55-4h | 457 | +0.044% | -0.005% | 0.58 | 99% | +0.41R | INCONCLUSIVE |
| VolBreakout-m1-1d | 352 | +0.015% | -0.007% | 0.45 | 100% | +0.16R | INCONCLUSIVE |
| VolBreakout-m1-4h | 1705 | -0.079% | -0.110% | -1.45 | 95% | -0.16R | FAIL |
| VolBreakout-m1.5-1d | 161 | +0.015% | -0.001% | 0.59 | 100% | +0.34R | INCONCLUSIVE |
| VolBreakout-m1.5-4h | 1049 | -0.028% | -0.053% | -0.63 | 100% | -0.09R | FAIL |
| VolBreakout-m2-1d | 85 | +0.004% | -0.006% | 0.22 | 99% | +0.16R | INCONCLUSIVE |
| VolBreakout-m2-4h | 507 | -0.000% | -0.017% | -0.00 | 99% | -0.00R | FAIL |

## support universe, gross fees

Reality-check p-value (family-wise, not a gate): 0.018. Equal-weight buy-and-hold: mean daily +0.268%, Sharpe 0.95.

| Config | Trades | Mean daily | 95% lower bound | Sharpe | Beats nulls | Mean R/trade | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MeanReversion-threshold10-1d | 181 | -0.002% | -0.004% | -0.26 | 44% | -0.03R | FAIL |
| MeanReversion-threshold10-4h | 1444 | +0.003% | -0.006% | 0.17 | 42% | +0.01R | FAIL |
| MeanReversion-threshold20-1d | 349 | +0.001% | -0.004% | 0.08 | 25% | +0.01R | FAIL |
| MeanReversion-threshold20-4h | 2658 | -0.001% | -0.016% | -0.04 | 98% | -0.00R | FAIL |
| MeanReversion-threshold5-1d | 92 | +0.000% | -0.002% | 0.04 | 86% | +0.01R | INCONCLUSIVE |
| MeanReversion-threshold5-4h | 697 | +0.001% | -0.005% | 0.10 | 69% | +0.01R | INCONCLUSIVE |
| TrendDonchian-n100-1d | 40 | +0.022% | -0.008% | 0.40 | 83% | +1.71R | INCONCLUSIVE |
| TrendDonchian-n100-4h | 282 | +0.074% | +0.023% | 0.94 | 100% | +1.04R | PASS_INSAMPLE |
| TrendDonchian-n20-1d | 151 | +0.031% | +0.005% | 0.73 | 99% | +0.74R | PASS_INSAMPLE |
| TrendDonchian-n20-4h | 1015 | +0.070% | +0.029% | 0.97 | 97% | +0.25R | PASS_INSAMPLE |
| TrendDonchian-n55-1d | 71 | +0.024% | -0.006% | 0.44 | 84% | +1.04R | INCONCLUSIVE |
| TrendDonchian-n55-4h | 457 | +0.071% | +0.021% | 0.95 | 100% | +0.63R | PASS_INSAMPLE |
| VolBreakout-m1-1d | 353 | +0.026% | +0.003% | 0.79 | 100% | +0.26R | PASS_INSAMPLE |
| VolBreakout-m1-4h | 2356 | +0.049% | +0.013% | 0.76 | 98% | +0.07R | PASS_INSAMPLE |
| VolBreakout-m1.5-1d | 162 | +0.020% | +0.003% | 0.80 | 100% | +0.45R | PASS_INSAMPLE |
| VolBreakout-m1.5-4h | 1085 | +0.057% | +0.032% | 1.27 | 100% | +0.18R | PASS_INSAMPLE |
| VolBreakout-m2-1d | 85 | +0.007% | -0.003% | 0.39 | 99% | +0.28R | INCONCLUSIVE |
| VolBreakout-m2-4h | 513 | +0.040% | +0.022% | 1.25 | 99% | +0.27R | PASS_INSAMPLE |
