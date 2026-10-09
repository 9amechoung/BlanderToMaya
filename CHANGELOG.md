# 변경 내역

예전 버전 파일은 모두 [`dist/`](dist/) 폴더에 남아 있어요.

## v0.8.5
[다운로드](dist/maya_style_v0.8.5.zip)
- **F키**: 아무것도 선택하지 않은 상태에서 누르면 장면 전체가 화면에 들어오게 맞춰요 (마야와 동일).
  오브젝트 모드와 컴포넌트(편집) 모드 모두 돼요. 선택한 게 있으면 지금처럼 선택한 것에 맞춰요. Shift+F는 4분할 모든 화면에 적용.

## v0.8.4
[다운로드](dist/maya_style_v0.8.4.zip)
- **Wireframe on Shaded 버튼**: 뷰포트 헤더 오른쪽 끝(셰이딩 버튼 옆)에 추가했어요. 솔리드 그대로 면 위에 엣지를 그려요 (투명해지지 않음). Display 메뉴에도 있어요.
- **툴 헤더가 잘리던 문제 수정**: 뷰포트가 좁으면 셸프 탭이 자동으로 드롭다운 하나로 줄어들어서, 오른쪽의 Orientation / Drag / 대칭(X Y Z) / Options가 다 보여요. 넓은 화면에서는 탭 그대로예요.
  휠클릭 축 표시도 `MMB: X` 대신 휠 아이콘 + `X`로 짧게 바꿨어요.

## v0.8.3
[다운로드](dist/maya_style_v0.8.3.zip)
- **뒤에 있는 것 선택 - X-ray 완전히 없이**: 이제 드래그하는 동안에도 X-ray가 켜지지 않아요.
  박스 / 올가미 안에 들어온 것을 애드온이 직접 계산해서, 화면은 솔리드 그대로인데 가려진 오브젝트와
  뒤쪽 버텍스·엣지·페이스까지 선택돼요. (버텍스: 박스 안의 점, 엣지: 박스에 닿거나 걸친 엣지, 페이스: 중심이 박스 안에 있는 면 - 마야 기본값과 같음)
  Shift(토글) / Ctrl(빼기) / Ctrl+Shift(추가) 드래그도 그대로 돼요.

## v0.8.2
[다운로드](dist/maya_style_v0.8.2.zip)
- **뒤에 있는 것도 드래그로 선택**: X-ray를 켜지 않아도 박스 / 올가미 선택이 가려진 오브젝트와 뒤쪽 버텍스·엣지·페이스까지 잡아요 (마야와 동일).
  드래그하는 동안만 X-ray가 잠깐 켜졌다가 끝나면 원래대로 돌아와요. 클릭 선택은 지금처럼 앞에 보이는 것만 골라요.
  설정의 "Select Through"로 끌 수 있어요.

## v0.8.1
[다운로드](dist/maya_style_v0.8.1.zip)
- **Freeze Transformations 수정**: 이제 마야처럼 Translate / Rotate / Scale만 0 / 0 / 1이 되고
  **피벗은 원래 자리에 그대로** 있어요. (이전에는 블렌더의 Apply가 피벗을 월드 중심으로 옮겼어요.)
  Reset Transformations: Translate를 하면 마지막으로 Freeze한 자리로 돌아가요 (마야와 같음).

## v0.8.0
[다운로드](dist/maya_style_v0.8.0.zip)
- 오른쪽 패널에 **로컬 / 월드(글로벌) 위치·회전·스케일**을 함께 표시, 둘 다 직접 입력해서 수정 가능
  - Channel Box (Local): 부모 기준 값
  - World Space (Global): 장면 기준 실제 값. 값을 바꾸면 부모가 있어도 그 위치로 정확히 옮겨짐
  - 컴포넌트 모드에서는 선택한 버텍스들의 중심 위치를 로컬 / 월드로 표시하고 수정 가능
  - 사이드바(N) Channel Box 탭에도 같은 내용

## v0.7.4
[다운로드](dist/maya_style_v0.7.4.zip)
- 4분할 뷰의 각 화면이 **자기 시점을 유지**: Top을 크게 봤다가 다시 4분할로 돌아와도 Perspective 화면은 Perspective 그대로예요.
  크게 본 상태에서 줌하거나 이동한 것도 그 화면에 그대로 남아요 (마야와 동일).

## v0.7.3
[다운로드](dist/maya_style_v0.7.3.zip)
- 4분할 뷰에서 마우스를 올린 화면 위에서 Space를 짧게 누르면 **그 화면이 단일 뷰로 커짐** (마야와 동일).
  이전에는 항상 원근(Perspective) 뷰로 돌아갔어요.

## v0.7.2
[다운로드](dist/maya_style_v0.7.2.zip)
- 고른 축을 마야처럼 **노란색으로 표시**: 이동/스케일 화살표, 평면 핸들, 회전 링, 가운데(자유 이동)
- **Q / W / E / R을 한 번 더 누르면** 휠클릭 축이 가운데(자유 이동)로 돌아감 (마야와 동일)
- 설정에 "Highlight Picked Axis" 켜기/끄기 추가

## v0.7.1
[다운로드](dist/maya_style_v0.7.1.zip)
- **Shift + 기즈모 화살표 드래그**로 익스트루드(컴포넌트 모드) / 복제(오브젝트 모드) — 마야와 같은 방식
  (이전 버전의 Shift + 휠클릭 익스트루드는 마야와 달라서 바꿨어요)
- **Shift + 휠클릭 드래그**: 처음 드래그한 방향의 축으로 고정해서 이동 (마야와 동일)
- 선택 규칙을 마야처럼: Shift 토글, Ctrl 선택 해제, Ctrl+Shift 추가 (클릭과 박스 선택 모두)

## v0.7.0
[다운로드](dist/maya_style_v0.7.0.zip) · 무엇이 바뀌었는지 전체 정리: [docs/CHANGES_KO.md](docs/CHANGES_KO.md)
- 마야 메뉴 전체 보강: 54개 메뉴, 블렌더 기능 255개 연결
  - File / Edit를 마야 메뉴로 교체 (Increment and Save, Export Selection, Delete by Type, Group / Ungroup, Duplicate with Transform...)
  - Modeling 메뉴셋에 Surfaces(Loft, Planar, Revolve, Extrude), Generate, Cache 추가
  - Animation 메뉴셋에 Audio, FX 메뉴셋(nParticles, Fluids, nCloth, nHair, Fields/Solvers, Effects), Rendering에 Toon, Stereo 추가
  - Booleans, Match Transformations, Add Attribute(채널 박스에 표시), Lattice, Nonlinear, Pole Vector, Quick Rig, Convert Selection 등 새 명령
  - 위쪽 메뉴에서 고른 명령이 3D 뷰포트에서 실행되도록 수정 (회색으로 막히던 항목 해결)
- 핫박스: Space를 누르고 있으면 모든 메뉴와 뷰 전환이 뜸 (짧게 누르면 4분할 뷰)
- Ctrl+우클릭 선택 변환 메뉴, Shift+우클릭이 버텍스 / 엣지 / 페이스마다 다른 메뉴로
- 단축키 추가: F2~F6 메뉴셋, Ctrl+F9~F11 변환, Ctrl+G 그룹, Shift+D, B 소프트 선택(+휠클릭 반경), D/Insert 피벗 편집, Alt+B 배경, 방향키 픽워크, , . 키 이동, Ctrl+E / Ctrl+B, > <, Ctrl+Shift+I, Z / Shift+Z 등
- 커맨드 라인(파이썬)을 타임라인 아래에 추가, 사이드바에 Modeling Toolkit 탭 추가
- 버그 수정: Group을 하면 오브젝트 위치가 밀리던 문제, Target Weld 때문에 메뉴가 안 열리던 문제

## v0.6.0
[다운로드](dist/maya_style_v0.6.0.zip)
- Ctrl+Shift+우클릭 툴 설정 마킹 메뉴 추가 (마야와 같은 배치)
  - Object / World / Component (= 블렌더 방향 Local / Global / Normal), Axis ▸, Symmetry ▸, Snap ▸, Keep Spacing
  - Select ▸, Selection Constraints ▸, Transform Constraints ▸, Shift Extrude, Shift Duplicate,
    Preserve UVs, Preserve Children, Tweak Mode, Move Options
- Shift + 휠클릭 드래그: 에딧 모드에서는 익스트루드, 오브젝트 모드에서는 복제한 뒤 이동 (v0.7.1에서 Shift + 기즈모 드래그로 변경)

## v0.5.0
[다운로드](dist/maya_style_v0.5.0.zip)
- 마야 인터페이스: 설치하면 `Maya` 워크스페이스가 만들어지고 자동으로 전환됨
  - 왼쪽 아웃라이너, 가운데 뷰포트와 툴박스, 오른쪽 채널 박스(속성 창 맨 위), 아래 타임라인
  - 마야 색상: 회색 뷰포트, 초록색 선택 표시
  - File → New를 하거나 다른 파일을 열어도 `Maya` 워크스페이스가 없으면 자동으로 추가됨
- 상단 바를 마야 메뉴바로 교체
  - File / Edit / Create / Select / Modify / Display / Windows + 메뉴셋 메뉴
  - 메뉴셋 드롭다운 (Modeling / Rigging / Animation / Rendering)으로 메뉴가 바뀜
  - 상태줄: 새 파일/열기/저장, 실행 취소/다시 실행, 오브젝트/버텍스/엣지/페이스, 그리드/커브/점/면 스냅, Symmetry, 렌더 버튼
  - 오른쪽에 `Workspace:` 선택
- 셸프를 마야처럼 탭 형식으로 변경 (설정에서 드롭다운으로 되돌릴 수 있음)
- 이동/회전/스케일 기즈모의 축을 **클릭만 해도** 휠클릭 드래그 축이 선택됨 (이전에는 드래그해야 했음)
- 우클릭 메뉴: 빠르게 탭해도 마야 메뉴가 열림, 목록이 일반 메뉴처럼 평평하게, 하위 메뉴에 ▸ 표시
- 블렌더 4.0, 4.1도 지원 (Add-ons 탭에서 설치)

## v0.4.0
[다운로드](dist/maya_style_v0.4.0.zip)
- 우클릭 메뉴: 오브젝트를 선택한 상태면 빈 공간에서 우클릭을 누르고 있어도 메뉴가 열림 (마야와 동일)
- 휠클릭(가운데 버튼) 드래그 추가: 이동/회전/스케일 툴에서 기즈모의 축(X/Y/Z, 평면)을 클릭한 뒤
  뷰포트 아무 데서나 휠클릭 드래그하면 그 축으로만 움직임
  - 셸프 바 오른쪽에 지금 선택된 축이 `MMB: X`처럼 표시됨
  - 애드온 설정의 "Middle-drag Along Picked Axis"로 켜고 끌 수 있음

## v0.3.0
[다운로드](dist/maya_style_v0.3.0.zip)
- 마야식 우클릭 메뉴 추가: 오브젝트 위에서 우클릭을 누르고 있으면 열림
  - 방사형 메뉴: Vertex, Edge, Face, Object Mode, UV ▸, Vertex Face, Multi
  - 아래 목록: 오브젝트 이름(속성 보기), Select, Select All, Deselect All, Select Hierarchy, Invert Selection, Select Similar,
    Inputs ▸, Paint ▸, UV Sets ▸, Material Attributes..., Assign New Material ▸, Assign Existing Material ▸
  - 에딧 모드에서는 Select Shell, Edge Loop, Edge Ring, Grow, Shrink 같은 컴포넌트 선택 메뉴로 바뀜
  - 빈 공간에서 우클릭하면 원래 블렌더 메뉴가 열림

## v0.2.0
[다운로드](dist/maya_style_v0.2.0.zip)
- 마야 단축키 추가
  - Space: 4분할 뷰 전환, Ctrl+Space: 뷰포트 최대화, Alt+V: 애니메이션 재생
  - Ctrl+Y 다시 실행, Alt+Shift+D 히스토리 삭제
  - 4/5/6/7 셰이딩 모드, 1/2/3 스무스 프리뷰
  - X/V/C 누르고 있는 동안 그리드/버텍스/엣지 스냅
  - Shift+H 다시 표시, Alt+H Isolate (마야식으로 수정)
- 애드온 설정의 "F8~F11 Component Hotkeys" 옵션이 "Maya Hotkeys"로 통합됨

## v0.1.0
[다운로드](dist/maya_style_v0.1.0.zip)
- 첫 버전
- Industry Compatible(마야식) 키맵 자동 적용
- 뷰포트 상단 셸프 바 (Poly Modeling, Edit Poly, Curves, UV, Rigging, Animation, Rendering)
- Shift+우클릭 마킹 메뉴 (오브젝트 모드, 에딧 모드)
- 채널 박스와 레이어 에디터 (N 패널)
- F8~F11 컴포넌트 모드
