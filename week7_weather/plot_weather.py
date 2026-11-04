"""수집 코드가 만든 CSV(같은 폴더, weather_<기간>.csv)를 읽어 시간-기온 선그래프를 그린다.

- 파일명·기간은 collect_weather.py의 CSV_PATH/TAG를 import해 쓰므로 두 코드의 이름이 항상 일치한다.
- API를 다시 호출하지 않고 이미 저장된 CSV만 사용한다.
- 시각을 시간 형식으로 바꾸고 시간순 정렬 후, 빠진 시각을 1시간 간격으로 채워
  기온 결측 구간에서는 선이 끊어지게 한다.
- temperature_<기간>.png로 저장하고 화면에도 띄운다.
"""

import csv
import math
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from collect_weather import CSV_PATH, TAG   # 수집 코드와 같은 파일명·기간 꼬리표 사용

HERE = Path(__file__).resolve().parent
PNG_PATH = HERE / f"temperature_{TAG}.png"

LINE_COLOR = "#2b6cb0"   # 단일 계열이므로 색 하나, 범례 없음
GRID_COLOR = "#d9dde3"   # 눈에 덜 띄는 격자
NAN = float("nan")


def read_weather(path):
    """CSV를 읽어 [(datetime, 기온 또는 NaN), ...]로 돌려준다.

    datetime 문자열은 시간 형식으로 바꾸고, 기온이 빈 값이면 NaN으로 둔다.
    (utf-8-sig로 저장된 파일이므로 BOM도 함께 처리한다.)
    """
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for rec in csv.DictReader(f):
            when = datetime.strptime(rec["datetime"], "%Y-%m-%d %H:%M")
            temp = rec["temperature_C"].strip()
            rows.append((when, float(temp) if temp else NAN))
    return rows


def sort_by_time(rows):
    """시간순(오름차순)으로 정렬한다."""
    return sorted(rows, key=lambda r: r[0])


def fill_hourly_gaps(rows):
    """첫 시각~마지막 시각 사이를 1시간 간격으로 훑어, 빠진 시각에 NaN 자리를 만든다.

    반환: (시각 목록, 기온 목록, 새로 만든 빈 시각 목록)
    """
    by_time = dict(rows)
    start, end = rows[0][0], rows[-1][0]
    times, temps, added = [], [], []
    current = start
    while current <= end:
        times.append(current)
        if current in by_time:
            temps.append(by_time[current])
        else:
            temps.append(NAN)   # NaN은 matplotlib에서 선을 끊는다
            added.append(current)
        current += timedelta(hours=1)
    return times, temps, added


def isolated_points(times, temps):
    """앞뒤가 모두 결측이라 선으로는 보이지 않는 단독 관측점을 찾는다 (점으로 표시용)."""
    xs, ys = [], []
    for i, t in enumerate(temps):
        if math.isnan(t):
            continue
        prev_nan = i == 0 or math.isnan(temps[i - 1])
        next_nan = i == len(temps) - 1 or math.isnan(temps[i + 1])
        if prev_nan and next_nan:
            xs.append(times[i])
            ys.append(t)
    return xs, ys


def draw(times, temps):
    """선그래프를 그려 Figure를 돌려준다 (제목·축 이름 지정, 격자·테두리는 옅게)."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(times, temps, color=LINE_COLOR, linewidth=2)

    xs, ys = isolated_points(times, temps)
    if xs:
        ax.plot(xs, ys, linestyle="none", marker="o", markersize=5, color=LINE_COLOR)

    ax.set_title("Temperature over time")
    ax.set_xlabel("Time (KST)")
    ax.set_ylabel("Temperature (°C)")

    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.grid(True, color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    fig.tight_layout()
    return fig


def main():
    if not CSV_PATH.exists():
        raise SystemExit(f"{CSV_PATH.name} 이(가) 없습니다. 먼저 collect_weather.py를 실행하세요.")
    rows = sort_by_time(read_weather(CSV_PATH))
    if not rows:
        raise SystemExit(f"{CSV_PATH.name}에 자료가 없습니다.")

    times, temps, added = fill_hourly_gaps(rows)
    missing_temp = sum(1 for t in temps if math.isnan(t))
    print(f"읽은 행: {len(rows)}, 그래프 시각 수(1시간 간격): {len(times)}")
    print(f"누락 시각(빈자리 추가): {len(added)}, 기온 결측(선 끊김 대상): {missing_temp}")

    fig = draw(times, temps)
    fig.savefig(PNG_PATH, dpi=150)
    print(f"저장 위치: {PNG_PATH}")
    plt.show()


if __name__ == "__main__":
    main()
