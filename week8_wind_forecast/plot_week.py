"""실습 4: 평가 첫 주(2024-12-01 00시 ~ 12-07 23시) 예측 비교 그래프.

실제값=검정, 현재 풍속 유지(기준)=회색 점선, 선형회귀=파랑.
MAE는 그래프 구간이 아니라 12월 1~31일 전체(744행)로 계산한다.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import mean_absolute_error

BASE = Path(__file__).parent

p = pd.read_csv(BASE / "predictions.csv", parse_dates=["forecast_time", "target_time"])

# MAE: 12월 전체
mae_base = mean_absolute_error(p["actual"], p["baseline_persistence"])
mae_lr = mean_absolute_error(p["actual"], p["linear_regression"])

# 그래프: 첫 주만
week = p[(p["target_time"] >= "2024-12-01 00:00") & (p["target_time"] <= "2024-12-07 23:00")]

fig, ax = plt.subplots(figsize=(12, 4.5), dpi=150)
ax.plot(week["target_time"], week["actual"], color="black", lw=1.8, label="Observed")
ax.plot(week["target_time"], week["baseline_persistence"], color="gray", lw=1.4,
        ls="--", label="Current wind baseline")
ax.plot(week["target_time"], week["linear_regression"], color="#2a5fa8", lw=1.8,
        label="Linear regression")

ax.set_xlabel("Target time (KST)")
ax.set_ylabel("Wind speed (m/s)")
ax.set_ylim(bottom=0)
ax.set_xlim(week["target_time"].min(), week["target_time"].max())
ax.xaxis.set_major_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
ax.grid(axis="y", color="#e5e5e5", lw=0.8)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=3, frameon=False)

fig.tight_layout()
fig.savefig(BASE / "prediction_week.png")

print(f"그래프 구간: {week['target_time'].min()} ~ {week['target_time'].max()}  ({len(week)}행)")
print(f"MAE 계산 구간: {p['target_time'].min()} ~ {p['target_time'].max()}  ({len(p)}행)")
print(f"MAE 현재 풍속 유지: {mae_base:.3f} m/s")
print(f"MAE 선형회귀      : {mae_lr:.3f} m/s")
print("저장: prediction_week.png")
