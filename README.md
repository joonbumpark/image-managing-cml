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
| `--algorithm` | `tolerance`(기본, 아래 설명) 또는 `gimp`(색상 오염 제거, tolerance/feather 무시) |
| `--tolerance` | (`tolerance` 알고리즘) 완전 투명 처리할 색상 거리 허용치 (0-100%, 기본 10) |
| `--feather` | (`tolerance` 알고리즘) 경계 밖으로 부드럽게 페이드아웃되는 폭 (0-100%, 기본 5). 0이면 경계가 딱딱하게 잘림 |
| `-f, --force` | 출력 파일이 이미 있어도 덮어쓰기 |

`--color`, `--pick`, `--from-corner` 중 아무것도 지정하지 않으면 기본값으로
좌상단(`top-left`) 코너 색을 자동 사용합니다.

**`--algorithm tolerance` (기본)**: 각 픽셀과 대상 색상 사이의 RGB 유클리드
거리를 0~100% 스케일로 정규화합니다. `tolerance` 이내면 완전 투명,
`tolerance` ~ `tolerance + feather` 구간은 선형으로 알파가 서서히 복원되며,
그 밖은 원본 그대로 유지됩니다. `feather`는 안티에일리어싱된 배경 경계를
자연스럽게 처리하기 위한 옵션입니다.

**`--algorithm gimp`**: GIMP의 "Color to Alpha"와 같은 방식의 색상 오염
제거(decontamination) 알고리즘입니다. 단순 거리 임계값이 아니라, 각 픽셀을
"대상 색상과 실제 전경색이 알파로 블렌딩된 결과"로 보고 채널별로 역산해서
알파와 전경색을 동시에 복원합니다. 흰 배경 위의 부드러운 흰색 테두리처럼
경계에 색이 번져 있는 경우, tolerance 방식보다 깨끗하게 제거됩니다. 대신
`tolerance`/`feather` 튜닝이 없고 완전 자동입니다.

```bash
imgedit color-to-alpha art.png --algorithm gimp --color "#ffffff"
```

### `crop` — 자르기 (박스 / 크기+앵커 / 자동 여백 제거)

```bash
# 좌표로 직접 자르기
imgedit crop art.png --box 10,10,500,500

# 크기 + 기준점으로 자르기
imgedit crop art.png --size 512x512 --anchor top

# 배경(투명 또는 특정 색) 여백을 자동으로 잘라내기 - color-to-alpha 다음 단계로 유용
imgedit crop art.png --auto
imgedit crop art.png --auto --padding 8
imgedit crop art.png --auto --bg-color "#ffffff" --tolerance 5
```

옵션:

| 옵션 | 설명 |
| --- | --- |
| `-o, --output PATH` | 출력 경로. 기본값은 `<입력파일명>.crop<확장자>` |
| `--box LEFT,TOP,RIGHT,BOTTOM` | 명시적 픽셀 좌표로 자르기 |
| `--size WxH` | 지정 크기로 자르기 (`--anchor`로 위치 지정) |
| `--anchor` | `center`(기본)/`top`/`bottom`/`left`/`right`/`top-left`/`top-right`/`bottom-left`/`bottom-right` |
| `--auto` | 피사체 주변의 균일한 여백을 자동으로 트림 |
| `--bg-color HEX` | `--auto`에서 사용할 배경색 (기본: 투명 픽셀, 없으면 좌상단 코너 색) |
| `--tolerance` | `--auto`에서 배경으로 간주할 색상 거리 허용치 (%, 기본 2) |
| `--padding` | `--auto` 결과 주변에 남길 여백 픽셀 수 |
| `-f, --force` | 출력 파일이 이미 있어도 덮어쓰기 |

`--box`, `--size`, `--auto` 중 정확히 하나만 지정해야 합니다.

### `resize` — 크기 조정

```bash
imgedit resize art.png --width 512
imgedit resize art.png --height 512
imgedit resize art.png --scale 0.5
imgedit resize art.png --max-side 1024
imgedit resize art.png --width 512 --height 512 --stretch
```

옵션:

| 옵션 | 설명 |
| --- | --- |
| `-o, --output PATH` | 출력 경로. 기본값은 `<입력파일명>.resize<확장자>` |
| `--width` / `--height` | 픽셀 단위 목표 크기. 하나만 주면 비율 유지, 둘 다 주면 기본적으로 비율을 유지한 채 박스 안에 맞춤(fit) |
| `--scale` | 배율 (예: `0.5` = 절반 크기). width/height/max-side와 함께 쓸 수 없음 |
| `--max-side` | 긴 변 기준 픽셀 수에 맞춰 비율 유지 리사이즈. width/height와 함께 쓸 수 없음 |
| `--stretch` | width/height를 둘 다 줬을 때 비율 무시하고 정확히 그 크기로 늘림 |
| `--filter` | 리샘플링 필터: `nearest`/`bilinear`/`bicubic`/`lanczos`(기본) |
| `-f, --force` | 출력 파일이 이미 있어도 덮어쓰기 |

### 파이프라인 예시

AI 생성 이미지의 흰 배경을 투명화 → 여백 자동 트림 → 리사이즈까지 한 번에:

```bash
imgedit color-to-alpha art.png --algorithm gimp -o step1.png
imgedit crop step1.png --auto --padding 8 -o step2.png
imgedit resize step2.png --max-side 1024 -o final.png
```

## 테스트

```bash
pytest
```

## 프로젝트 구조

```
src/imgedit/
  cli.py                      # click 기반 CLI 진입점 (서브커맨드 등록)
  color_utils.py              # 색상 문자열 파싱 유틸
  geometry_utils.py           # 박스/크기 문자열 파싱 유틸
  core/color_to_alpha.py      # color-to-alpha 알고리즘 (tolerance + gimp)
  core/crop.py                # crop 알고리즘 (box / size+anchor / autocrop)
  core/resize.py              # resize 알고리즘
  commands/color_to_alpha.py  # color-to-alpha CLI 서브커맨드
  commands/crop.py            # crop CLI 서브커맨드
  commands/resize.py          # resize CLI 서브커맨드
tests/
```

새 편집 기능을 추가할 때는 `core/`에 순수 함수로 알고리즘을 구현하고,
`commands/`에 이를 감싸는 click 서브커맨드를 만든 뒤 `cli.py`의
`main.add_command(...)`에 등록하면 됩니다.
