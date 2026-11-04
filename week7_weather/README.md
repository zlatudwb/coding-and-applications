# 서울(108) 기온 수집·시각화

기상청 API허브의 지상관측 시간자료로 일주일치 기온·습도·풍속을 모아 CSV로 정리하고, 시간–기온 선그래프를 그립니다.

## 데이터

| 항목 | 내용 |
|---|---|
| 관측소 | 108 (서울) |
| 기간 | 2026-01-20 00:00 ~ 2026-01-26 23:00 (KST), 1시간 간격 168행 |
| 출처 | 기상청 API허브 지상관측 시간자료(기간 조회) `kma_sfctm3.php` — https://apihub.kma.go.kr |
| 사용 항목 | TM(관측시각), TA(기온 ℃), HM(상대습도 %), WS(풍속 m/s) |

## 파일

| 파일 | 설명 |
|---|---|
| `collect_weather.py` | API 호출 → 응답 검증 → `weather_20260120_20260126.csv` 저장 |
| `plot_weather.py` | CSV를 읽어 `temperature_20260120_20260126.png` 저장·표시 (API 재호출 없음) |
| `weather_20260120_20260126.csv` | `datetime, temperature_C, humidity_pct, wind_speed_ms` (UTF-8 BOM, 결측은 빈 값) |
| `temperature_20260120_20260126.png` | Temperature over time 선그래프 |

## 실행 방법

```bash
pip install requests matplotlib
python collect_weather.py   # 실행 중 터미널에서 API 인증키를 입력 (화면에 표시되지 않음)
python plot_weather.py
```

- 인증키는 [API허브](https://apihub.kma.go.kr)에서 발급받아 `collect_weather.py` 실행 중 `getpass` 프롬프트에만 입력합니다. 코드·CSV·이미지·README 어디에도 키를 저장하지 않으며, 오류가 나도 키와 키가 포함된 요청 주소는 출력하지 않습니다.
- 기간을 바꾸려면 `collect_weather.py`의 `TM1`, `TM2`(최대 31일), 관측소는 `STN`을 수정합니다. 파일 이름은 기간에 맞춰 자동으로 바뀌고 `plot_weather.py`도 같은 이름을 사용합니다.

## 확인 결과

- **누락·결측:** 168개 시각 중 빠진 시각과 기온·습도·풍속 결측은 모두 0건이었고, 기온 −9.0℃ 두 건(01-25 07·08시)은 결측 코드(−9.0)와 표기가 같지만 같은 행의 이슬점·습도가 정상이어서 실제 관측값으로 처리했습니다.
- **그래프 해석:** 기온은 새벽(05~08시)에 최저, 오후(15~16시)에 최고가 되는 하루 주기를 반복하며, 1월 22일 아침 −13.1℃로 가장 낮았다가 23일 오후 0.2℃까지 올랐고 일주일 내내 대체로 영하권이었습니다.
