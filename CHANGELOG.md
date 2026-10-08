# 변경 내역

예전 버전 파일은 모두 [`dist/`](dist/) 폴더에 남아 있어요.

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
