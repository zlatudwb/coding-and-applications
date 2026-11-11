"""실습 1: asos_108_2023_2024.csv 상태 확인 (원본은 수정하지 않음)."""
from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).parent / "asos_108_2023_2024.csv"

df = pd.read_csv(CSV_PATH)
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime").reset_index(drop=True)  # 메모리 상에서만 정렬

first, last = df["datetime"].iloc[0], df["datetime"].iloc[-1]
n_rows = len(df)
n_dup = int(df["datetime"].duplicated().sum())

# 1시간 격자 기준으로 행이 없는 시각
full_grid = pd.date_range(first, last, freq="h")
missing_times = full_grid.difference(pd.DatetimeIndex(df["datetime"]))

# 기존 행 안의 빈칸
blank_counts = df[["temperature_C", "humidity_pct", "wind_speed_ms"]].isna().sum()

print("=== 처음 3행 ===")
print(df.head(3).to_string(index=False))
print()
print("=== 검사 결과 ===")
print(f"처음 시각        : {first}")
print(f"마지막 시각      : {last}")
print(f"전체 행 수       : {n_rows:,}")
print(f"중복 시각 수     : {n_dup}")
print(f"1시간 격자 시간 수: {len(full_grid):,}")
print(f"행이 없는 시각 수 : {len(missing_times)}")
print()
print("=== 기존 행 안의 빈칸 수 ===")
print(f"풍속(wind_speed_ms)  : {blank_counts['wind_speed_ms']}")
print(f"기온(temperature_C)  : {blank_counts['temperature_C']}")
print(f"습도(humidity_pct)   : {blank_counts['humidity_pct']}")
print()
print("=== 행이 없는 시각 목록 ===")
# 연속 구간으로 묶어서 출력
runs = []
for t in missing_times:
    if runs and t - runs[-1][1] == pd.Timedelta(hours=1):
        runs[-1][1] = t
    else:
        runs.append([t, t])
for start, end in runs:
    n = int((end - start) / pd.Timedelta(hours=1)) + 1
    print(f"{start} ~ {end}  ({n}시간)")
