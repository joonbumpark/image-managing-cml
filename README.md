# imgedit

AI 생성 이미지를 편집하기 위한 커맨드라인 이미지 편집 툴킷입니다.
매 명령이 인터랙티브 프롬프트 없이 한 줄로 끝나도록 설계해서, 사람이 직접
써도 되고 AI 에이전트가 쉘 명령으로 호출하기도 쉽습니다.

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

설치 후 `imgedit` 명령을 바로 사용할 수 있습니다.

## 명령어

### `color-to-alpha` — 특정 색상을 알파 0(투명)으로

AI로 생성한 이미지는 흔히 단색 배경(흰색, 초록색 등)을 갖습니다. 이 명령은
지정한 색상과 가까운 픽셀들을 투명하게 만들어 PNG로 저장합니다.

```bash
# 가장 간단한 사용: 좌상단 코너 픽셀 색을 자동으로 배경색으로 인식
imgedit color-to-alpha art.png

# 색상을 직접 지정
imgedit color-to-alpha art.png --color "#ffffff" --tolerance 15

# 특정 픽셀 좌표에서 색을 샘플링
imgedit color-to-alpha art.png --pick 2,2

# 다른 코너에서 샘플링 + 출력 경로 지정
imgedit color-to-alpha art.png --from-corner bottom-right -o out.png

# 기존 파일 덮어쓰기
imgedit color-to-alpha art.png -f
```

옵션:

| 옵션 | 설명 |
| --- | --- |
| `-o, --output PATH` | 출력 경로. 기본값은 `<입력파일명>.alpha.png` |
| `--color HEX` | 대상 색상 직접 지정 (`#rrggbb` 또는 `#rgb`) |
| `--pick X,Y` | 해당 픽셀의 색을 대상 색상으로 샘플링 |
| `--from-corner CORNER` | `top-left`/`top-right`/`bottom-left`/`bottom-right` 코너에서 샘플링 |
| `--tolerance` | 완전 투명 처리할 색상 거리 허용치 (0-100%, 기본 10) |
| `--feather` | tolerance 경계 밖으로 부드럽게 페이드아웃되는 폭 (0-100%, 기본 5). 0이면 경계가 딱딱하게 잘림 |
| `-f, --force` | 출력 파일이 이미 있어도 덮어쓰기 |

`--color`, `--pick`, `--from-corner` 중 아무것도 지정하지 않으면 기본값으로
좌상단(`top-left`) 코너 색을 자동 사용합니다.

동작 방식: 각 픽셀과 대상 색상 사이의 RGB 유클리드 거리를 0~100% 스케일로
정규화합니다. `tolerance` 이내면 완전 투명, `tolerance` ~ `tolerance + feather`
구간은 선형으로 알파가 서서히 복원되며, 그 밖은 원본 그대로 유지됩니다.
`feather`는 AI 이미지 특유의 안티에일리어싱된 배경 경계를 자연스럽게
처리하기 위한 옵션입니다.

## 테스트

```bash
pytest
```

## 프로젝트 구조

```
src/imgedit/
  cli.py                      # click 기반 CLI 진입점 (서브커맨드 등록)
  color_utils.py              # 색상/좌표 문자열 파싱 유틸
  core/color_to_alpha.py      # 순수 알고리즘 (PIL.Image -> PIL.Image)
  commands/color_to_alpha.py  # color-to-alpha CLI 서브커맨드
tests/
```

새 편집 기능을 추가할 때는 `core/`에 순수 함수로 알고리즘을 구현하고,
`commands/`에 이를 감싸는 click 서브커맨드를 만든 뒤 `cli.py`의
`main.add_command(...)`에 등록하면 됩니다.
