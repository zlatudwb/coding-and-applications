# 코딩과 응용 실습

국립공주대학교 코딩과 응용(2008424) 실습 저장소입니다. 주차별로 폴더를 나누어 프로그램을 추가해 왔고, 각 폴더의 README에 실행 방법과 사용법이 있습니다.

## 폴더 구조

```text
coding-and-applications/         (저장소 최상위)
├─ README.md                    전체 개요와 주차별 변경 기록
├─ week4_force_converter/       Week 4  힘 단위 변환기
├─ week5_load_analyzer/         Week 5  CSV 하중·응력 분석
├─ week6_section_gui/           Week 6  단면 선택과 CSV 분석 GUI
│  └─ submission/               Week 6 과제 제출 자료(실행 화면, 검증 결과)
└─ week7_weather/               Week 7  기상청 API 기온 수집·그래프
```

| 주차 | 폴더 | 프로그램 | 실행 | 설명 |
|---|---|---|---|---|
| Week 4 | [week4_force_converter](week4_force_converter/) | `force_converter.py`, `calculator_gui.py` | `python force_converter.py`, `python calculator_gui.py` | [README](week4_force_converter/README.md) |
| Week 5 | [week5_load_analyzer](week5_load_analyzer/) | `load_analyzer.py` | `python load_analyzer.py` | [README](week5_load_analyzer/README.md) |
| Week 6 | [week6_section_gui](week6_section_gui/) | `load_analyzer_gui.py` | `python load_analyzer_gui.py` | [README](week6_section_gui/README.md) |
| Week 7 | [week7_weather](week7_weather/) | `collect_weather.py`, `plot_weather.py` | `python collect_weather.py`, `python plot_weather.py` | [README](week7_weather/README.md) |

Week 6 과제 제출 자료(실행 화면, 단면적 검증, 응력 비교, 오류 처리 결과)는 [week6_section_gui/submission](week6_section_gui/submission/README.md)에 정리했습니다.

각 프로그램은 해당 폴더 안에서 실행합니다. Week 5, Week 6은 `matplotlib`가 필요합니다(`python -m pip install matplotlib`). Week 7은 `requests`도 필요하며(`python -m pip install requests matplotlib`), API 인증키는 실행 중 터미널에서 입력하고 저장소에는 포함하지 않습니다.

## 주차별 변경 기록

| 일자 | 주차 | 내용 | 추가·변경한 파일 | 커밋 |
|---|---|---|---|---|
| 2026-09-30 | Week 4 | 힘 단위 변환기: 터미널 버전과 GUI 계산기 | `week4_force_converter/force_converter.py`, `week4_force_converter/calculator_gui.py` | `d832436` Initial commit |
| 2026-10-07 | Week 5 | CSV 하중 데이터에서 응력 계산, 최대값 찾기, 시간–응력 그래프 저장 | `week5_load_analyzer/` 의 `load_analyzer.py`, `load_data.csv`, `load_test.csv`, `load_bad.csv`, `load_result.csv`, `stress_plot.png` | `8974569` Add CSV stress analysis and plot |
| 2026-10-14 | Week 6 | 단면 선택과 CSV 분석 GUI: 사각형·원형봉·원형관·사각형관·H형강의 단면적과 최대 응력 계산 | `week6_section_gui/load_analyzer_gui.py` | `4d46602` Add section selection and CSV analysis GUI |
| 2026-10-14 | 정리 | README에 주차별 변경 기록 추가 | `README.md` | `c82ce2a` Organize README with weekly change log |
| 2026-10-14 | Week 6 | 화면 배율과 크기에 맞게 GUI 창 크기 조정 | `week6_section_gui/load_analyzer_gui.py` | `90b2860` Fit GUI window size to screen scale |
| 2026-10-14 | 정리 | 파일을 주차별 폴더로 이동하고 README를 폴더별로 분리 (파일 내용은 그대로) | 전체 | `c8034d0` Reorganize files into week folders |
| 2026-10-14 | Week 6 | 과제 제출 자료 정리: 실행 화면, 단면적 검증, 응력 비교, 오류 처리 결과 | `week6_section_gui/submission/` | `e1b97bf` Add Week 6 submission materials |
| 2026-11-04 | Week 7 | 기상청 API허브 시간자료(서울 108, 2026-01-20~26) 수집, CSV 정리, 시간–기온 그래프 | `week7_weather/` | `f739505` Add Week 7 KMA weather collection and temperature plot |

위 표의 파일 위치는 현재 폴더 구조 기준입니다. 폴더 정리 전에는 모든 파일이 저장소 최상위에 있었습니다. 파일 이동은 Git이 이름 변경으로 기록하므로, 각 파일의 이력은 `git log --follow <파일>`로 이어서 볼 수 있습니다.

Week 6에서 구현한 내용(실습 1~4):

1. **CSV 선택과 기본 창**: 찾아보기 버튼, 읽기 전용 경로칸, 유효 데이터 수, 시간–하중 그래프
2. **사각형 단면**: 폭 b와 높이 h(mm)로 단면적을 계산하고, 분석 버튼으로 최대 응력과 발생 시간을 표시, 그래프를 시간–응력으로 갱신
3. **나머지 단면**: 원형봉, 원형관, 사각형관, H형강 추가. 선택한 단면에 필요한 입력칸만 표시
4. **불가능한 치수 처리**: 빈칸·문자·0·음수와 내부 공간이 없는 치수를 안내하고 계산을 중단. 조건이 바뀌면 이전 결과를 무효로 표시
