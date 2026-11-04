"""기상청 API허브 지상관측 시간자료(기간 조회, kma_sfctm3) 수집·정리 스크립트.

- 관측소 108, 2026-01-20 00:00 ~ 2026-01-26 23:00 (KST)  (기간은 TM1/TM2에서 변경)
- 인증키는 실행 중 getpass로 입력받으며, 키와 키가 포함된 요청 주소는
  오류 상황을 포함해 어디에도 출력하지 않는다.
- 결과: weather_<시작일>_<종료일>.csv (datetime, temperature_C, humidity_pct, wind_speed_ms)
        raw_response_<시작일>_<종료일>.txt (서버가 보낸 원본 응답 그대로)
- 자료가 없는 응답은 CSV로 저장하지 않고 원인을 안내한 뒤 중단한다.

응답 형식 (실제 응답 기준)
  '#'으로 시작하는 줄 = 설명줄. 그중 '# 12. TA : 기온 (C)' 같은 줄이
  '헤더 번호 : 변수명' 표이고, 자료 행은 공백으로 구분된 값이 그 번호 순서로 나온다.
  결측은 -9 / -9.0 / -9.00 (열 서식에 따라 다름), 일부 항목은 -99로 표기된다.
"""

import csv
import getpass
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

BASE_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"
STN = "108"
TM1 = "202601200000"   # 시작 (KST)
TM2 = "202601262300"   # 종료 (KST)
TAG = f"{TM1[:8]}_{TM2[:8]}"   # 기간 꼬리표: 파일명에 사용 (plot_weather.py도 이 값을 가져다 씀)
TIMEOUT = (5, 30)  # (연결, 읽기) 초
HEAD_LINES = 15
DATA_ROWS = 3

OUT_DIR = Path(__file__).resolve().parent
RAW_PATH = OUT_DIR / f"raw_response_{TAG}.txt"
CSV_PATH = OUT_DIR / f"weather_{TAG}.csv"   # plot_weather.py가 같은 이름을 import해 읽는다

# CSV 열 이름 -> (API 변수명, 공식 설명서의 헤더 번호). 번호는 실제 응답 헤더와 대조해 검증한다.
COLUMNS = [
    ("datetime", "TM", 1),
    ("temperature_C", "TA", 12),
    ("humidity_pct", "HM", 14),
    ("wind_speed_ms", "WS", 4),
]

# 결측 코드. 기온도 이 값만 결측으로 보고, 그 밖의 음수(영하 기온)는 정상값으로 유지한다.
MISSING_CODES = {-9.0, -99.0}


# ---------------------------------------------------------------- 요청/응답 읽기

def get_charset(response):
    """Content-Type 헤더에서 charset을 꺼낸다. 없으면 None."""
    match = re.search(r"charset=([\w\-]+)", response.headers.get("Content-Type", ""), re.I)
    return match.group(1) if match else None


def decode_body(response):
    """응답 바이트를 charset(헤더 -> EUC-KR -> UTF-8 순)에 맞춰 문자열로 바꾼다."""
    for charset in (get_charset(response), "euc-kr", "utf-8"):
        if not charset:
            continue
        try:
            return response.content.decode(charset), charset
        except (UnicodeDecodeError, LookupError):
            continue
    return response.content.decode("utf-8", errors="replace"), "utf-8(replace)"


def extract_message(text):
    """실패 응답에서 message를 찾는다 (JSON이면 message 키, 아니면 본문 앞부분)."""
    try:
        data = json.loads(text)
    except ValueError:
        return text.strip()[:300] or "(본문 없음)"
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "message" in node:
                return str(node["message"])
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return text.strip()[:300]


def redact(text, key):
    """출력 직전에 혹시 섞인 인증키를 가린다."""
    return text.replace(key, "***") if key else text


def fail(message):
    print(f"[실패] {message}")
    sys.exit(1)


def fetch(auth_key):
    """API를 호출해 (본문 문자열, 원본 바이트)를 돌려준다. 실패하면 안내 후 종료."""
    params = {"tm1": TM1, "tm2": TM2, "stn": STN, "help": "1", "authKey": auth_key}
    try:
        response = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        fail("요청 시간이 초과되었습니다. 잠시 후 다시 시도하세요.")
    except requests.exceptions.RequestException as exc:
        # 예외 메시지에는 키가 든 요청 주소가 들어갈 수 있어 종류만 출력한다.
        fail(f"요청 중 오류가 발생했습니다. ({type(exc).__name__})")

    print(f"HTTP 상태: {response.status_code} {response.reason}")
    text, charset = decode_body(response)
    text = redact(text, auth_key)
    print(f"응답 charset: {charset}")

    if response.status_code != 200 or text.lstrip().startswith("{"):
        fail(f"API 오류 메시지: {redact(extract_message(text), auth_key)}")

    raw = response.content.replace(auth_key.encode("utf-8"), b"***")
    return text, raw


def save_raw(raw):
    """원본 응답 바이트를 가공 없이 보관한다 (나중에 재파싱·검증용)."""
    RAW_PATH.write_bytes(raw)


# ---------------------------------------------------------------- 파싱

def split_lines(text):
    """설명줄('#'로 시작)과 자료 행을 구분한다."""
    comment_lines, data_lines = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        (comment_lines if line.lstrip().startswith("#") else data_lines).append(line)
    return comment_lines, data_lines


def preview(text, data_lines):
    """본문 앞 15줄과 실제 자료 행 3개를 따로 보여 준다."""
    print(f"\n===== 본문 앞 {HEAD_LINES}줄 =====")
    for line in text.splitlines()[:HEAD_LINES]:
        print(line)
    print(f"\n===== 실제 데이터 행 {DATA_ROWS}개 =====")
    if not data_lines:
        print("(자료 행이 없습니다.)")
    for line in data_lines[:DATA_ROWS]:
        print(line)


def parse_header(comment_lines):
    """'# 12. TA : 기온 (C)' 형태의 줄에서 {변수명: 헤더 번호}를 만든다."""
    header = {}
    for line in comment_lines:
        match = re.match(r"^#\s*(\d+)\.\s*([A-Za-z0-9_]+)\s*:", line)
        if match:
            header[match.group(2)] = int(match.group(1))
    return header


def check_positions(header):
    """TM(1), WS(4), TA(12), HM(14)의 위치가 실제 응답 헤더와 같은지 확인한다."""
    print("\n===== 헤더 번호 확인 =====")
    for _, name, expected in COLUMNS:
        actual = header.get(name)
        status = "일치" if actual == expected else "불일치"
        print(f"{name}: 설명서 {expected}번 / 실제 응답 {actual}번 -> {status}")
        if actual != expected:
            fail(f"{name}의 헤더 번호가 예상과 다릅니다. 열 위치를 확인하세요.")


def clean_value(token):
    """측정값 토큰을 정리한다.

    - 결측 코드(-9, -9.0, -9.00, -99 ...) 또는 숫자가 아님 -> '' (빈 값)
    - 그 밖의 값(영하 기온 포함)은 원래 표기 그대로 유지
    """
    try:
        number = float(token)
    except ValueError:
        return ""
    return "" if number in MISSING_CODES else token


def clean_temperature(tokens, header):
    """기온(TA) 토큰을 정리한다. 영하 기온과 결측 코드(-9.0)를 구분하는 규칙이 핵심.

    -9.0은 결측 코드이면서 실제 -9.0도 관측값일 수도 있어 글자만으로는 구분되지 않는다.
    그래서 같은 행의 이슬점(TD)과 습도(HM)가 정상값이면 '관측이 있었던 행'으로 보고
    -9.0을 실제 기온으로 인정한다. 둘 중 하나라도 결측이면 결측으로 처리한다.
    -9.0 이외의 음수는 언제나 정상값이다.
    """
    token = tokens[header["TA"] - 1]
    if clean_value(token) != "":
        return token
    try:
        is_minus9 = float(token) == -9.0
    except ValueError:
        return ""
    if is_minus9 and all(clean_value(tokens[header[n] - 1]) != "" for n in ("TD", "HM")):
        return token
    return ""


def parse_rows(data_lines, header):
    """공백으로 자른 자료 행에서 필요한 열만 뽑아 행 목록(dict)을 만든다.

    반환: (행 목록, 형식 오류로 제외한 행 수)
    """
    needed = max(max(num for _, _, num in COLUMNS), header.get("TD", 0))
    rows, bad_rows = [], 0
    for line in data_lines:
        tokens = line.split()
        if len(tokens) < needed:
            bad_rows += 1
            continue
        try:
            when = datetime.strptime(tokens[header["TM"] - 1], "%Y%m%d%H%M")
        except ValueError:
            bad_rows += 1
            continue
        record = {"datetime": when}
        for col, name, _ in COLUMNS[1:]:
            if name == "TA":
                record[col] = clean_temperature(tokens, header)
            else:
                record[col] = clean_value(tokens[header[name] - 1])
        rows.append(record)
    return rows, bad_rows


# ---------------------------------------------------------------- 정리/저장

def sort_and_dedupe(rows):
    """시각 오름차순으로 정렬하고 같은 시각의 중복 행은 첫 행만 남긴다.

    반환: (정리된 행, 제거한 중복 수, 중복인데 값이 서로 다른 건수)
    """
    rows = sorted(rows, key=lambda r: r["datetime"])
    kept, removed, conflicts = [], 0, 0
    for row in rows:
        if kept and kept[-1]["datetime"] == row["datetime"]:
            removed += 1
            if kept[-1] != row:
                conflicts += 1
            continue
        kept.append(row)
    return kept, removed, conflicts


def ensure_has_data(data_lines, rows, bad_rows):
    """자료가 없는 응답이면 CSV를 만들지 않고 원인을 안내한 뒤 중단한다."""
    if not data_lines:
        fail(
            "응답에 자료 행이 없습니다. CSV는 저장하지 않았습니다.\n"
            f"  원인 후보: 조회 기간({TM1}~{TM2})에 해당 관측소({STN})의 자료가 없거나,\n"
            "  아직 수집되지 않은 기간이거나, 지점번호가 잘못되었을 수 있습니다.\n"
            f"  응답 원문은 {RAW_PATH} 에서 확인하세요."
        )
    if not rows:
        fail(
            f"자료 행 {len(data_lines)}개가 있었지만 형식이 맞지 않아 읽을 수 없습니다"
            f"(제외 {bad_rows}행). CSV는 저장하지 않았습니다.\n"
            "  원인 후보: 열 개수나 시각(TM) 형식이 설명서와 다릅니다.\n"
            f"  응답 원문은 {RAW_PATH} 에서 확인하세요."
        )
    value_cols = [col for col, _, _ in COLUMNS[1:]]
    if all(r[col] == "" for r in rows for col in value_cols):
        fail(
            f"자료 행 {len(rows)}개의 기온·습도·풍속이 모두 결측입니다. CSV는 저장하지 않았습니다.\n"
            "  원인 후보: 해당 기간에 관측값이 없거나 관측 장비 점검 중이었을 수 있습니다.\n"
            f"  응답 원문은 {RAW_PATH} 에서 확인하세요."
        )


def save_csv(rows):
    """CSV_PATH(weather_<기간>.csv)로 저장한다 (행 인덱스 없음, utf-8-sig)."""
    names = [col for col, _, _ in COLUMNS]
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["datetime"] = row["datetime"].strftime("%Y-%m-%d %H:%M")
            writer.writerow(out)


def report(rows, removed, conflicts, bad_rows):
    """행수, 열별 결측수, 첫/마지막 시각, 저장 위치 등을 출력한다."""
    names = [col for col, _, _ in COLUMNS]
    print("\n===== 정리 결과 =====")
    print(f"행 수: {len(rows)}")
    print("열별 결측 수:")
    for col in names:
        print(f"  {col}: {sum(1 for r in rows if r[col] == '')}")
    print(f"첫 시각: {rows[0]['datetime']:%Y-%m-%d %H:%M}")
    print(f"마지막 시각: {rows[-1]['datetime']:%Y-%m-%d %H:%M}")
    span_hours = int((rows[-1]["datetime"] - rows[0]["datetime"]) / timedelta(hours=1)) + 1
    print(f"1시간 간격 기준 누락 시각 수: {span_hours - len(rows)}")
    print(f"제거한 중복 행: {removed} (값이 달랐던 중복: {conflicts})")
    print(f"형식 오류로 제외한 행: {bad_rows}")
    negatives = sum(1 for r in rows if r["temperature_C"].startswith("-"))
    print(f"영하 기온(정상값으로 유지): {negatives}건")
    print(f"원본 응답 저장 위치: {RAW_PATH}")
    print(f"CSV 저장 위치: {CSV_PATH}")


def main():
    auth_key = getpass.getpass("API 인증키를 입력하세요 (화면에 표시되지 않습니다): ").strip()
    if not auth_key:
        fail("인증키가 입력되지 않았습니다.")

    text, raw = fetch(auth_key)
    save_raw(raw)

    comment_lines, data_lines = split_lines(text)
    preview(text, data_lines)
    if not data_lines:
        ensure_has_data(data_lines, [], 0)  # 자료 없음 -> 원인 안내 후 중단 (CSV 미저장)

    header = parse_header(comment_lines)
    check_positions(header)

    rows, bad_rows = parse_rows(data_lines, header)
    ensure_has_data(data_lines, rows, bad_rows)

    rows, removed, conflicts = sort_and_dedupe(rows)
    save_csv(rows)
    report(rows, removed, conflicts, bad_rows)


if __name__ == "__main__":
    main()
