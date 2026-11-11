"""실습 3: 현재 풍속 유지(기준) vs 선형회귀 비교.

학습 : 정답 시각(target_time)이 2023-01 ~ 2024-11 인 행
평가 : 정답 시각이 2024-12-01 ~ 2024-12-31 인 행 (KST)
평가 중에는 모델을 다시 학습하지 않는다.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

BASE = Path(__file__).parent
FEATURES = ["wind_now", "wind_lag1", "wind_lag2", "temp_now", "humidity_now"]

df = pd.read_csv(BASE / "wind_dataset.csv", parse_dates=["forecast_time", "target_time"])
df = df.sort_values("target_time").reset_index(drop=True)  # 시간순

# 정답 시각 기준으로 학습/평가 분리
train = df[df["target_time"] < "2024-12-01"]
test = df[(df["target_time"] >= "2024-12-01") & (df["target_time"] < "2025-01-01")]

# 선형회귀: 학습 구간에서만 fit, 평가 구간은 predict만
model = LinearRegression().fit(train[FEATURES], train["wind_target"])
lr_pred = np.clip(model.predict(test[FEATURES]), 0, None)  # 음수 예측은 0으로

# 기준 예측: 1시간 뒤에도 현재 풍속 유지
base_pred = test["wind_now"].to_numpy()

actual = test["wind_target"].to_numpy()
mae_base = mean_absolute_error(actual, base_pred)
mae_lr = mean_absolute_error(actual, lr_pred)

pred = pd.DataFrame(
    {
        "forecast_time": test["forecast_time"].to_numpy(),
        "target_time": test["target_time"].to_numpy(),
        "actual": actual,
        "baseline_persistence": base_pred,
        "linear_regression": lr_pred,
    }
)
pred.to_csv(BASE / "predictions.csv", index=False)

print(f"학습 행 수: {len(train):,}  ({train['target_time'].min()} ~ {train['target_time'].max()})")
print(f"평가 행 수: {len(test):,}  ({test['target_time'].min()} ~ {test['target_time'].max()})")
print()
print("회귀 계수:")
for name, coef in zip(FEATURES, model.coef_):
    print(f"  {name:13s} {coef:+.4f}")
print(f"  {'intercept':13s} {model.intercept_:+.4f}")
print(f"음수 예측을 0으로 바꾼 행 수: {int((model.predict(test[FEATURES]) < 0).sum())}")
print()
print(f"MAE 현재 풍속 유지: {mae_base:.3f} m/s")
print(f"MAE 선형회귀      : {mae_lr:.3f} m/s")
print(f"선형회귀가 기준보다 {(1 - mae_lr / mae_base) * 100:.1f}% 작음")
print()
print("=== 첫 평가 결과 ===")
print(pred.head(1).to_string(index=False))
