"""선택 실습: 같은 입력·학습/평가 기간으로 랜덤포레스트를 추가해 세 방법 비교.

랜덤포레스트 설정: 나무 100개, 최대 깊이 6, 리프 최소 표본 5개, random_state=42
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

BASE = Path(__file__).parent
FEATURES = ["wind_now", "wind_lag1", "wind_lag2", "temp_now", "humidity_now"]

df = pd.read_csv(BASE / "wind_dataset.csv", parse_dates=["forecast_time", "target_time"])
df = df.sort_values("target_time").reset_index(drop=True)

# 실습 3과 동일한 분리 (정답 시각 기준)
train = df[df["target_time"] < "2024-12-01"]
test = df[(df["target_time"] >= "2024-12-01") & (df["target_time"] < "2025-01-01")]
actual = test["wind_target"].to_numpy()

base_pred = test["wind_now"].to_numpy()

lr = LinearRegression().fit(train[FEATURES], train["wind_target"])
lr_pred = np.clip(lr.predict(test[FEATURES]), 0, None)

rf = RandomForestRegressor(
    n_estimators=100, max_depth=6, min_samples_leaf=5, random_state=42
).fit(train[FEATURES], train["wind_target"])
rf_pred = np.clip(rf.predict(test[FEATURES]), 0, None)  # 같은 규칙: 음수는 0

mae = {
    "현재 풍속 유지": mean_absolute_error(actual, base_pred),
    "선형회귀": mean_absolute_error(actual, lr_pred),
    "랜덤포레스트": mean_absolute_error(actual, rf_pred),
}

print(f"학습 {len(train):,}행 / 평가 {len(test):,}행 (12월 1~31일, 같은 행으로 세 방법 비교)")
print()
print(f"{'방법':<10}{'12월 MAE':>12}{'기준 대비':>12}")
for name, v in mae.items():
    rel = (1 - v / mae["현재 풍속 유지"]) * 100
    print(f"{name:<10}{v:>10.4f} m/s{rel:>+10.1f}%")
print()
diff = mae["선형회귀"] - mae["랜덤포레스트"]
print(f"선형회귀 - 랜덤포레스트 MAE 차이: {diff:+.4f} m/s")
print()
print("랜덤포레스트 입력 중요도:")
for name, imp in sorted(zip(FEATURES, rf.feature_importances_), key=lambda x: -x[1]):
    print(f"  {name:13s} {imp:.3f}")
