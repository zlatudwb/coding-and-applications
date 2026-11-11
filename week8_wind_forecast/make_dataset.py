"""실습 2: 입력 5개 + 정답 1개를 한 행에 맞춘 wind_dataset.csv 만들기.

입력 : 현재 풍속·기온·습도, 정확히 1시간 전·2시간 전 풍속
정답 : 정확히 1시간 뒤의 실제 풍속 (입력에는 포함하지 않음)
빠진 시각은 빈 행으로 넣어 1시간 간격을 먼저 맞추고, 빈 값은 채우지 않는다.
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
SRC = BASE / "asos_108_2023_2024.csv"
OUT = BASE / "wind_dataset.csv"

df = pd.read_csv(SRC, parse_dates=["datetime"]).set_index("datetime").sort_index()

# 1) 1시간 간격 복원 (빠진 시각은 NaN 행으로 추가, 값은 채우지 않음)
grid = pd.date_range(df.index.min(), df.index.max(), freq="h")
full = df.reindex(grid)
full.index.name = "datetime"
n_grid = len(full)

# 2) 입력·정답 열 만들기 (shift는 행 위치가 아니라 1시간 격자 기준이라 정확히 N시간 차이)
data = pd.DataFrame(
    {
        "forecast_time": full.index,                       # 예측하는 시각
        "target_time": full.index + pd.Timedelta(hours=1),  # 맞힐 시각
        "wind_now": full["wind_speed_ms"],
        "wind_lag1": full["wind_speed_ms"].shift(1),
        "wind_lag2": full["wind_speed_ms"].shift(2),
        "temp_now": full["temperature_C"],
        "humidity_now": full["humidity_pct"],
        "wind_target": full["wind_speed_ms"].shift(-1),
    }
)

# 3) 입력이나 정답이 비어 있는 행만 제외
feature_cols = ["wind_now", "wind_lag1", "wind_lag2", "temp_now", "humidity_now"]
before = len(data)
data = data.dropna(subset=feature_cols + ["wind_target"]).reset_index(drop=True)

data.to_csv(OUT, index=False)

print(f"시간 간격을 맞춘 뒤의 행 수: {n_grid:,}")
print(f"제외된 행 수             : {before - len(data):,}")
print(f"저장된 행 수             : {len(data):,}  -> {OUT.name}")
print()
print("=== 첫 4행 ===")
print(data.head(4).to_string(index=False))
