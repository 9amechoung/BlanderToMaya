# BlanderToMaya: Maya Style UI for Blender

블렌더를 마야처럼 쓰게 해 주는 애드온이에요. 설치하면 마야식 화면 배치, 메뉴바, 키맵, 셸프, 마킹 메뉴, 채널 박스가 한 번에 세팅돼요.

![Maya 워크스페이스](docs/screenshot_layout.png)

> **무엇이 바뀌었는지 전체 정리 (원래 블렌더 → 마야처럼 바꾼 것, 불가능한 것):** [docs/CHANGES_KO.md](docs/CHANGES_KO.md)

## 다운로드 및 설치

1. 최신 버전 [`dist/maya_style_v0.12.5.zip`](dist/maya_style_v0.12.5.zip)을 다운로드합니다. 파일을 연 뒤 **Download raw file** 버튼을 누르면 돼요. **압축은 풀지 마세요.**
   - 예전 버전은 [`dist/`](dist/) 폴더에, 버전별 변경 내용은 [CHANGELOG.md](CHANGELOG.md)에 있어요.
2. 블렌더를 엽니다. **4.0 이상**을 지원해요.
3. `Edit → Preferences → Get Extensions` 화면에서 오른쪽 위 `⌄` 메뉴를 열고 **Install from Disk...**를 누른 뒤 zip을 선택합니다.
   (4.0, 4.1 또는 구버전 방식: `Add-ons` 탭 → **Install...** 또는 `⌄` → **Install from Disk...** → 목록에서 체크)
4. 설치되면 바로 `Maya` 워크스페이스로 바뀌고, 키맵이 **Industry Compatible**(마야식)로 바뀌어요.
5. 새 버전으로 업데이트할 때도 같은 방법으로 새 zip을 설치하면 이전 버전을 덮어써요.

## 기능

### 0. 마야 인터페이스
- **화면 배치**: 왼쪽 아웃라이너, 가운데 뷰포트(왼쪽에 툴박스), 오른쪽 채널 박스, 아래 타임라인
  - 오른쪽은 블렌더 속성 창이에요. Object 탭 맨 위에 채널 박스가 있고, 아래쪽에 Layer Editor가 있어요. 다른 탭은 마야의 Attribute Editor 역할이에요.
  - 원래 블렌더 화면은 위쪽 `Workspace:`에서 `Layout`을 고르면 돼요.
  - 화면이 망가지면 `Windows → Reset Maya Workspace`를 누르세요.
  - 워크스페이스는 .blend 파일마다 저장돼요. 그래서 새 파일이나 다른 사람 파일을 열면 `Maya` 워크스페이스를 자동으로 추가해요. 설정에서 끌 수 있어요.
- **메뉴바**: `File Edit Create Select Modify Display Windows` + 메뉴셋 메뉴 + `Help`
  - 메뉴셋 드롭다운이나 **F2~F6**으로 바꾸면 뒤쪽 메뉴가 바뀌어요.
    - **Modeling**: Mesh, Edit Mesh, Mesh Tools, Mesh Display, Curves, Surfaces, Deform, UV, Generate, Cache
    - **Rigging**: Skeleton, Skin, Deform, Constrain, Control, Cache
    - **Animation**: Key, Playback, Audio, Visualize, Deform, Constrain, Cache
    - **FX**: nParticles, Fluids, nCloth, nHair, Fields/Solvers, Effects, Cache
    - **Rendering**: Lighting/Shading, Texturing, Render, Toon, Stereo
  - 원래 블렌더 메뉴는 File / Edit / Help 맨 아래에 "Blender ... Menu"로 남겨 뒀어요.
  - **옵션 박스(□)**: 설정이 있는 메뉴 항목 오른쪽에 □ 버튼이 있어요. 누르면 명령을 실행하고 설정 창(Adjust Last Operation)이 바로 떠요. 값을 바꾸면 결과에 바로 반영돼요.
  - **Space를 누르고 있으면 핫박스**가 떠요. 모든 메뉴와 뷰 전환(Top / Front / Side / Perspective)을 커서 근처에서 쓸 수 있어요.
- **상태줄**: 메뉴바 옆
  - 새 파일, 열기, 저장, 실행 취소, 다시 실행
  - 오브젝트, 버텍스, 엣지, 페이스 모드
  - 그리드, 커브, 점, 면 스냅 토글
  - Symmetry X, 렌더, IPR, 렌더 설정
  - **Input Line** (맨 오른쪽): 왼쪽 아이콘으로 모드를 고르고 입력한 뒤 Enter
    - Select by Name: `pCube*` 처럼 이름으로 선택 (`*`, `?` 가능, 띄어서 여러 개)
    - Rename: 선택한 오브젝트 이름 바꾸기. 여러 개면 `name1, name2...`, `#`을 넣으면 그 자리에 번호 (`leg_##` → `leg_01`)
    - Absolute / Relative: `1 2 3`처럼 입력하면 지금 툴(이동/회전/스케일)에 따라 그 값으로 / 그만큼 바꿔요. `.`은 그 축을 그대로 둬요.
- **뷰포트 패널 메뉴**: 뷰포트마다 위쪽에 마야처럼 `View Shading Lighting Show Renderer Panels` 메뉴가 있어요.
  - View: 프레이밍, Top/Front/Side 뷰, Focal Length, Near/Far Clip, Image Plane
  - Shading: 4~7 셰이딩, Wireframe on Shaded, X-Ray, X-Ray Joints, Backface Culling, 스무스 프리뷰
  - Lighting: Use Default Lighting / Use All Lights / Flat, Shadows
  - Show: 오브젝트 종류별 표시(Polygons, NURBS, Joints, Locators, Lights, Cameras...), All / None, Grid, HUD, Isolate Select
  - Renderer: Solid / Material Preview / Rendered, 렌더 엔진
  - Panels: Perspective(카메라 목록에서 Look Through), Orthographic, Look Through Selected, 4분할, **Tear Off Copy**(새 창으로 복사)
  - 블렌더 원래 메뉴(View, Select, Add, Object...)는 맨 끝 **Blender** 메뉴 안에 있어요.
- **Script Editor** (`Windows → Script Editor`): 새 창 위쪽은 히스토리(Info), 아래쪽은 입력(Text Editor)이에요. **Ctrl+Enter** 또는 숫자패드 Enter로 실행해요. 일부를 선택하면 선택한 줄만 실행하고, `print` 결과와 오류는 위쪽 히스토리에 나와요.
- **선택한 오브젝트에 와이어프레임**: 마야처럼 선택한 오브젝트는 셰이딩 위에 와이어가 겹쳐 보여요. 마지막에 선택한 것은 초록색, 나머지는 흰색이에요.
- **새 씬 기본값**: 새 파일은 마야처럼 길이 단위 **cm**, 프레임 **1~120**, **24fps**, 카메라와 뷰포트 **35mm**로 시작해요. 블렌더 1 유닛은 그대로 1m라서 화면에는 100cm로 보이고, FBX로 마야에 보내면 크기가 똑같이 나와요. 이미 있는 파일은 바꾸지 않아요 (`File → Maya Scene Defaults`로 지금 씬에 적용할 수 있어요).
- **마야 색상**: 회색 뷰포트, 선택한 오브젝트는 초록색, 버텍스는 보라색 점(선택하면 노랑), 선택한 엣지와 페이스는 주황색, 타임 슬라이더의 키는 빨간색. 블렌더 색으로 돌아가려면 설정에서 **Reset Blender Colors**를 누르세요.
- **셸프**: 마야처럼 탭으로 되어 있어요.

### 1. 마야식 단축키
설치하면 키맵이 한 번 자동으로 **Industry Compatible**로 바뀌고, 그 위에 마야 단축키를 덮어씌워요.

**화면 조작**
| 키 | 기능 |
|---|---|
| Alt + 좌클릭 드래그 | 회전 (Tumble) |
| Alt + 휠클릭 드래그 | 이동 (Track) |
| Alt + 우클릭 드래그 | 확대/축소 (Dolly) |
| F | 선택한 것을 화면 중앙에 (아무것도 선택 안 했으면 전체를 화면에) |
| A | 전체 오브젝트를 화면 중앙에 |
| Space | 4분할 뷰 ↔ 단일 뷰 (4분할일 때는 마우스를 올린 화면이 커지고, 각 화면은 자기 시점을 유지) |
| Ctrl + Space | 뷰포트 최대화 |

**기본 조작 및 편집**
| 키 | 기능 |
|---|---|
| Q / W / E / R | 선택 / 이동 / 회전 / 스케일 |
| Ctrl + Z / Ctrl + Y | 실행 취소 / 다시 실행 |
| G | 직전 명령 반복 |
| Ctrl + D | 복제 |
| Shift + P | 부모 해제 |
| Alt + Shift + D | 히스토리 삭제 (모디파이어 적용) |
| Alt + V | 애니메이션 재생 (Space를 4분할 뷰에 쓰기 때문에 마야처럼 Alt+V로 옮김) |

**디스플레이 / 셰이딩**
| 키 | 기능 |
|---|---|
| 4 | 와이어프레임 |
| 5 | 셰이드 (Solid) |
| 6 | 텍스처 (Material Preview) |
| 7 | 라이팅 (Rendered) |

**컴포넌트 / 스무스 프리뷰**
| 키 | 기능 |
|---|---|
| F8 | 오브젝트 ↔ 컴포넌트 모드 전환 |
| F9 / F10 / F11 | 버텍스 / 엣지 / 페이스 |
| 1 | 스무스 끄기 (원본 폴리곤) |
| 2 | 케이지 + 스무스 |
| 3 | 스무스 |

스무스 프리뷰는 선택한 메시에 `Smooth Preview`라는 Subdivision 모디파이어를 붙였다 뗐다 하는 방식이에요.

**스냅 (누르고 있는 동안만)**
| 키 | 기능 |
|---|---|
| X | 그리드 스냅 |
| V | 버텍스 스냅 |
| C | 커브(엣지) 스냅 |

키를 누른 채로 이동하면 스냅되고, 키를 떼면 원래 스냅 설정으로 돌아가요.

**숨기기 / 표시**
| 키 | 기능 |
|---|---|
| Ctrl + H | 선택한 것 숨기기 |
| Shift + H | 숨긴 것 다시 표시 |
| Alt + H | 선택한 것만 남기고 숨기기 (Isolate) |
| **Ctrl + 1** | **Isolate Select**: 이 뷰포트에서 선택한 것만 보기, 한 번 더 누르면 전부 다시 보기. 오브젝트 모드는 오브젝트, 컴포넌트 모드는 선택한 면·엣지·버텍스만 보여줘요. 카메라는 움직이지 않아요 (마야와 같음) |

원래 블렌더 키맵으로 돌리려면 애드온 설정에서 **Restore Blender Keymap**을 누르고 **Maya Hotkeys**를 끄세요.

### 2. 셸프 바 (뷰포트 상단)
왼쪽 드롭다운에서 셸프를 고르면 오른쪽 아이콘 줄이 바뀌어요.

| 셸프 | 내용 |
|---|---|
| Poly Modeling | 큐브, 구, 실린더 등 기본 도형 생성, Combine, Separate, Smooth, Mirror, Boolean, Center Pivot, Freeze, Delete History |
| Edit Poly | 버텍스/엣지/페이스 모드, Extrude, Bevel, Inset, Insert Edge Loop, Multi-Cut, Bridge, Fill Hole, Merge, Target Weld |
| Curves | 베지어/NURBS 커브, 원, 패스, 텍스트, NURBS 서피스 |
| UV | Unfold, Automatic, Cube/Cylinder/Sphere/Planar 투영, Cut/Sew |
| Rigging | 조인트, 로케이터, Parent, Bind Skin, IK, 각종 Constraint, 포즈/웨이트 페인트 모드 |
| Animation | Set Key, Delete Key, 재생과 키프레임 이동, Motion Trail, Bake |
| Rendering | 카메라, 라이트, 와이어프레임/셰이딩/텍스처/렌더 뷰, 렌더 |
| **Custom** | 내가 만드는 셸프 (아래 참고) |

아이콘에 마우스를 올리면 설명이 나와요. 글자를 같이 보고 싶으면 설정에서 **Show Button Labels**를 켜세요.

**Custom 셸프에 버튼 추가하기** (마야의 Ctrl+Shift+클릭 / 스크립트를 셸프로 드래그)
- 메뉴 항목이나 아무 버튼 위에서 **우클릭 → Add to Shelf (Custom)**
- Custom 셸프의 **+** 버튼: 파이썬 한 줄 명령으로 버튼 만들기
- Text Editor / Script Editor에서 **Text → Add Script to Shelf**: 지금 열린 스크립트 전체를 버튼으로
- Custom 셸프 버튼 위에서 우클릭: **Remove from Shelf**, Move Left / Move Right
- 블렌더 설정 폴더(`maya_style_shelf.json`)에 저장돼서 어떤 파일을 열어도 같은 셸프가 나와요.

### 3. 우클릭 메뉴 (오브젝트 위에서 우클릭을 누르고 있기)
마야처럼 오브젝트 위에서 우클릭을 **누르고 있으면** 메뉴가 열려요. 원하는 항목 위에서 버튼을 떼면 실행돼요. 짧게 클릭하면 메뉴가 열린 채로 남아 있어요.

```
┌───────────────────────┐
│ Cube...               │  ← 속성 보기 (Attribute Editor)
│ Select / Select All   │
│ Deselect All          │
│ Select Hierarchy      │
│ Invert Selection      │
│ Select Similar        │
│ Inputs ▸  Paint ▸     │
│ UV Sets ▸             │
│ Material Attributes...│
│ Assign New Material ▸ │  ← Lambert / Blinn / Phong / Standard Surface
│ Assign Existing ▸     │
└───────────────────────┘   [Edge]
                                       [Object Mode]
               [Vertex]       ●          [UV ▸]
               [Vertex Face]             [Multi]
                            [Face]
```
- **Face**(아래)는 페이스만 선택해요. 아래로 휙 긋기만 해도 Face가 골라져요. **Vertex Face**(왼쪽 아래)는 버텍스와 페이스 선택을 함께 켜고, **Multi**는 버텍스, 엣지, 페이스 선택을 모두 켜요.
- 오브젝트 메뉴 목록은 왼쪽 위에 있어요. 에딧 모드에서는 이 목록이 Select Shell, Edge Loop, Edge Ring, Grow, Shrink 같은 컴포넌트용으로 바뀌어요. 이때 Assign Material은 선택한 페이스에만 적용돼요.
- 메뉴 항목들이 커서에서 멀리 떨어져 있어서(기본 170px, 블렌더는 100px) 잘못 고르기 어려워요. 설정의 **Marking Menu Size**로 더 넓히거나 좁힐 수 있어요. Shift+우클릭, 핫박스 같은 다른 마킹 메뉴에도 똑같이 적용돼요.
- 오브젝트가 선택되어 있으면 **빈 공간**에서 우클릭을 누르고 있어도 선택한 오브젝트의 메뉴가 열려요. 아무것도 선택하지 않았으면 원래 블렌더 메뉴가 열려요.

![우클릭 메뉴](docs/screenshot_rmb_menu.png)

### 휠클릭 드래그로 축 고정 이동 (이동/회전/스케일 툴)
1. W/E/R로 이동, 회전, 스케일 툴을 고릅니다.
2. 기즈모에서 원하는 축(예: 빨간 X 화살표, 회전이면 링)을 **한 번 클릭**합니다. 드래그해도 돼요.
3. 이제 뷰포트 **아무 데서나 휠클릭 드래그**하면 그 축으로만 움직여요.
- 고른 축은 기즈모 위에 **노란색**으로 표시되고, 셸프 바 오른쪽에도 휠클릭 아이콘과 `X`처럼 표시돼요.
- **W / E / R을 한 번 더 누르면** 축 선택이 가운데(자유 이동)로 돌아가요.
- 기즈모 가운데(자유 이동)를 클릭하면 `Free`로 돌아가요. 평면 핸들을 클릭하면 `XY plane`처럼 평면 이동이 돼요.
- 축은 마지막으로 그 툴로 움직인 방향을 기억해요. 기즈모 대신 오브젝트를 직접 끌어서 움직였다면 `Free`로 바뀌어요.

### 툴 설정 메뉴 (Ctrl+Shift+우클릭)
마야처럼 Ctrl+Shift+우클릭을 하면 이동 툴 설정 메뉴가 열려요.

![툴 설정 메뉴](docs/screenshot_tool_menu.png)

| 메뉴 | 블렌더에서 하는 일 |
|---|---|
| Object / World / Component | 기즈모 방향 Local / Global / Normal |
| Axis ▸ | 방향 전체 목록 (World, Object, Component, Parent, Gimbal, View, 3D 커서) |
| Symmetry ▸ | 메시 대칭 X / Y / Z, Topology |
| Snap ▸ | 그리드, 커브(엣지), 점, 면 스냅 |
| Keep Spacing | 켜면 스냅할 때 선택한 것들이 간격을 유지한 채 함께 움직여요. 끄면 버텍스가 하나씩 따로 면에 붙어요. |
| Select ▸ | 선택, 올가미, 페인트 선택, 트윅, 이동, 회전, 스케일 툴 |
| Selection Constraints ▸ | 엣지 루프, 엣지 링, 경계, 셸 선택 |
| Transform Constraints ▸ | 엣지 슬라이드, 버텍스 슬라이드, 면 위로 투영 |
| Shift Extrude / Shift Duplicate | Shift를 누른 채 기즈모 화살표를 드래그하면 익스트루드 / 복제하며 이동 |
| Preserve UVs | UV를 유지하면서 이동 (Correct Face Attributes) |
| Preserve Children | 부모만 움직이고 자식은 제자리 (Affect Only Parents) |
| Tweak Mode | 트윅 툴로 전환 |
| Move Options | 속성 창의 툴 설정 탭 열기 |

### Shift + 드래그 (마야와 같은 동작)
- **Shift + 기즈모 화살표(또는 링, 스케일 핸들) 좌클릭 드래그**
  - 컴포넌트 모드: 선택한 면이나 엣지를 **익스트루드**하면서 그 축으로 이동해요.
  - 오브젝트 모드: 오브젝트를 **복제**하면서 그 축으로 이동해요.
  - 툴 설정 메뉴(Ctrl+Shift+우클릭)의 Shift Extrude / Shift Duplicate로 끌 수 있어요.
- **Shift + 휠클릭 드래그**: 처음 드래그한 방향에 가까운 축으로 고정해서 움직여요.
- **선택**: Shift+클릭은 토글, Ctrl+클릭은 선택 해제, Ctrl+Shift+클릭은 추가예요. 박스 선택도 똑같이 동작해요.
- **뒤에 있는 것도 선택**: 박스나 올가미로 드래그하면 X-ray를 켜지 않아도 가려진 오브젝트와 뒤쪽 버텍스·엣지·페이스까지 선택돼요. 화면은 X-ray 없이 그대로예요 (드래그하는 동안에도 투명해지지 않아요). 클릭은 앞에 보이는 것만 골라요.

### Connect (엣지를 잡고 슬라이스)
`Edit Mesh → Connect`, 엣지 모드 **Shift+우클릭 메뉴**, Edit Poly 셸프, Modeling Toolkit에 있어요. 아무것도 합치지 않고, 고른 엣지를 **가로질러 새 엣지를 잘라 넣어요** (마야와 같음).
- **엣지**: 엣지 링(나란한 엣지들)을 고르면 그 가운데를 지나는 새 루프가 한 바퀴 잘려 들어가요. 코너의 두 엣지는 대각선으로 잘려요. 새로 생긴 엣지가 선택돼요. 버텍스 선택 모드에서 엣지 링을 골라도 똑같이 잘라요.
- **버텍스**: 같은 면에 있는 버텍스끼리 면을 똑바로 잘라요.
- **페이스**: 면을 엣지 가운데로 잘라서 나눠요.
- **Segments**(몇 줄 넣을지)와 **Slide**(한쪽으로 밀기)는 옵션 박스(□)나 F9(Adjust Last Operation)에서 바로 바꿔요. Slide는 링 전체가 같은 방향으로 움직여요.

### 4. 마킹 메뉴 (Shift+우클릭)
- **오브젝트 모드**: 기본 도형 생성, 아래쪽에 Smooth, Combine, Center Pivot, Freeze, Delete History 같은 버튼 묶음
- **에딧 모드**: Extrude, Bevel, Insert Edge Loop, Multi-Cut, Target Weld, Inset, Edge Slide, 아래쪽에 Bridge, Fill, Merge 같은 버튼 묶음

### 5. 채널 박스 (N 패널 → Channel Box 탭)
- Translate, Rotate, Scale, Visibility를 마야처럼 한 줄씩 보여줘요. Rotate 아래에 **Rotate Order**가 있어요.
- SHAPES(메시 이름)와 INPUTS(모디파이어 = 마야의 히스토리)도 함께 보여줘요.
- **채널 선택**: 채널 이름(Translate X...)을 클릭하면 선택돼요. Ctrl+클릭은 토글, Shift+클릭은 범위 선택, 선택한 채널을 다시 클릭하면 해제돼요.
- **버추얼 슬라이더**: 채널을 고른 뒤 뷰포트에서 **휠클릭 드래그**(좌우)하면 값이 바뀌어요. Ctrl은 천천히, Shift는 빠르게. 선택한 오브젝트 모두에 적용돼요.
- 채널 박스 위쪽 메뉴
  - **Channels**: Key Selected, Key All, Break Connections(키와 드라이버 삭제), Mute / Unmute, **Lock / Unlock**, **Hide**, Lock and Hide
  - **Edit**: Add Attribute, Delete Attributes, Set Driven Key(드라이버), Graph Editor
  - **Show**: 숨긴 채널 다시 보이기
  - 잠긴 채널은 회색으로 바뀌고 입력이 막혀요. 키가 있는 채널은 블렌더가 칸 색으로 보여줘요 (키 있음: 초록 / 지금 프레임에 키: 노랑 / 드라이버: 보라).
- **Layer Editor**: 컬렉션 숨기기와 렌더 토글, 선택한 오브젝트로 새 레이어 만들기
  - 이름 앞의 칸을 누르면 마야처럼 **빈칸(보통) → T(Template: 회색 와이어, 선택 안 됨) → R(Reference: 셰이딩 그대로, 선택 안 됨)** 순서로 바뀌어요.
- **World Space (Global)**: 채널 박스 아래에 월드 기준 Translate / Rotate / Scale이 있어요. 채널 박스 값은 부모 기준(Local)이고, 여기 값은 장면 기준이에요. 둘 다 직접 입력해서 바꿀 수 있어요.
- 컴포넌트 모드에서는 선택한 버텍스들의 중심 위치를 Local / World로 보여주고, 숫자를 입력해서 옮길 수 있어요.

### 6. 프로젝트 (File → Project Window / Set Project)
마야처럼 프로젝트 폴더를 만들고, 그 안의 경로가 자동으로 잡혀요.
- **Project Window...**: 프로젝트 이름과 위치를 넣고 OK(Accept)를 누르면 마야와 같은 폴더(scenes, assets, images, sourceimages, renderData, clips, sound, scripts, data, movies, Time Editor, autosave, sceneAssembly)와 `workspace.mel`을 만들고 그 프로젝트로 설정해요. 폴더 이름은 창에서 바꿀 수 있고, **New** 버튼은 기본값으로 다시 채워요.
- **Set Project...**: 이미 있는 프로젝트 폴더를 골라요. **마야에서 만든 프로젝트도 그대로 쓸 수 있어요** (`workspace.mel`을 읽어요). `workspace.mel`이 없으면 기본 내용으로 만들어요.
- **Recent Projects**: 최근 프로젝트 목록. File 메뉴 위쪽에 지금 프로젝트가 표시돼요.
- 프로젝트가 설정되면 자동으로:
  - Open Scene(Ctrl+O), 새 장면 Save(Ctrl+S), Save As(Ctrl+Shift+S) → `scenes` 폴더에서 시작
  - 텍스처 이미지 열기 → `sourceimages`, 사운드 → `sound`
  - 렌더 출력 → `images` (렌더 경로를 직접 바꾼 장면은 그대로 둬요)
  - 자동 저장 → `autosave`
- 프로젝트 안에 있는 .blend 파일을 열면 그 프로젝트로 자동 설정돼요.

### 7. 애니메이션
- **타임 슬라이더 우클릭 메뉴**: Set Key, Delete, Copy, Paste, Tangents, Range Slider 설정, Auto Key, 프레임 레이트, Playblast
- 타임 슬라이더에서 **Shift+드래그**: 그 프레임 범위의 키를 선택해요 (마야와 같음). 선택한 키는 우클릭 메뉴나 Dope Sheet에서 옮겨요.
- **Graph Editor 탄젠트 버튼** (헤더 오른쪽): Auto, Spline, Linear, Flat, Stepped, Break Tangents, Unify Tangents
- Graph Editor / Dope Sheet에서 **휠클릭 드래그**: 선택한 키 이동
- Range Slider는 블렌더 타임라인의 Preview Range(시계 아이콘 옆 Start / End)예요.

### 8. Quick Select Set
- `Create → Sets: Quick Select Set...`: 선택한 오브젝트를 이름 붙여 저장해요. 컴포넌트 모드에서는 선택한 버텍스로 만들어요 (버텍스 그룹).
- `Edit → Quick Select Sets`: 목록에서 고르면 다시 선택돼요. Shift를 누르고 고르면 지금 선택에 추가해요.

### 9. 마야로 보내기 / 마야에서 가져오기 (FBX)
블렌더는 Z축이 위고 마야는 Y축이 위예요. 블렌더 안에서는 그대로 쓰고, 마야로 보낼 때만 맞추면 돼요.
- `File → Export to Maya (FBX: Y-up, cm)...` / `Export Selection to Maya...`: 마야에서 열면 **Y-up, cm**, 오브젝트 **회전 0 / 스케일 1**로 깨끗하게 들어가요.
  - 그냥 FBX로 내보내면 마야에서 오브젝트마다 Rotate X -90, Scale 100이 붙는데, 이 설정은 그 값을 지오메트리 쪽으로 넣어요.
  - 스무딩 그룹 포함, 조인트 끝의 `_end` 본 없음, 지금 애니메이션만 내보내요.
  - 조인트(아마추어)가 있으면 리깅이 깨지지 않게 "Apply Transform"은 자동으로 꺼요 (블렌더가 아마추어에서는 깨진다고 경고하는 옵션이에요). 이때는 최상위 오브젝트에 축 변환(Rotate X -90)과 스케일이 남을 수 있어요.
- `File → Import from Maya (FBX)...`: 조인트 방향 자동 맞춤, 끝 본 무시, 노멀 유지. 축은 파일에 적힌 대로 자동으로 바뀌어요.
- `Cache → USD: Export to Maya (Y-up)...`도 있어요.

### 10. UV Editor
`UV → UV Editor`(또는 오브젝트 우클릭 메뉴, UV 셸프)를 누르면 마야처럼 **UV Editor가 새 창으로** 열리고 오른쪽에 **UV Toolkit**이 있어요. 오브젝트 모드에서 열면 자동으로 컴포넌트 모드로 들어가고, 아무것도 선택 안 했으면 전체 UV를 보여줘요.

**UV Toolkit** (UV Editor 오른쪽, N 패널의 UV Toolkit 탭)
| 섹션 | 내용 |
|---|---|
| Select | UV / Edge / Face / Shell 선택 방식, Select Shell, Overlapping, Similar, Grow / Shrink, Select in Viewport too(동기화) |
| Transform | 90° 회전, Flip U / V, **Align U·V Min / Avg / Max**, Straighten, Orient Shells, 픽셀에 스냅 |
| Create | Automatic, Planar, Cube, Cylindrical, Spherical, Contour Stretch |
| Cut and Sew | **Cut**, **Sew**, **Move and Sew**, Split, Merge |
| Unfold | **Unfold**(셸 위치 그대로), Optimize, Unwrap(0~1로 다시 배치) |
| Arrange and Layout | Layout, **Stack**(셸 겹치기), **Normalize**(0~1 채우기), Match Scale |
| Texel Density | 맵 크기(px)를 넣고 **Get / Set** (px/cm). Set은 선택한 셸마다 크기를 맞춰요 |
| Display | **Checker Map**, **Texture Borders**(셸 경계 굵게), Distortion, Shaded UVs |

**UV Editor 단축키**
| 키 | 기능 |
|---|---|
| 우클릭 누르고 있기 | UV / Edge / Face / UV Shell / Object Mode 마킹 메뉴 |
| Shift + 우클릭 | Cut, Sew, Unfold, Layout, Rotate 90°, Move and Sew, Flip U, Straighten |
| Ctrl + 우클릭 | 선택 변환: To UVs / Edges / Faces / Shell / Edge Loop / Edge Ring |
| 휠클릭 드래그 | 지금 툴로 이동 / 회전 / 스케일 |
| X / V 누르고 있기 | 그리드 / UV 점 스냅 |
| **Shift + X** | Cut (선택한 UV 엣지 자르기) |
| **Shift + S** | Sew (선택한 UV 엣지 붙이기) |
| **Ctrl + L** | Layout |
| **Ctrl + U** | Unfold |
| **Ctrl + Shift + X** | 선택한 면으로 새 UV 셸 만들기 (Create UV Shell) |
| F / A | 선택 / 전체 프레이밍 |

Shift+X, Shift+S, Ctrl+L, Ctrl+U, Ctrl+Shift+X는 마야 UV Editor 기본 단축키와 같아요. UV Editor 안에서만 동작해요 (3D 뷰포트의 단축키는 그대로예요).

- **Unfold**는 마야처럼 셸이 있던 자리와 크기를 그대로 두고 펴요. 블렌더 Unwrap은 전부 0~1로 다시 배치해 버려서 따로 만들었어요. 선택하지 않은 셸은 움직이지 않아요.
- **Cut**은 고른 UV 엣지를 셸 경계로 만들어요 (블렌더에서는 심으로 저장돼요). 그다음 Unfold하면 그 엣지에서 갈라져요. **Sew**는 다시 붙이고 심도 지워요.
- 색은 마야처럼 UV 점은 보라색(선택하면 초록), 셸 면은 파란색으로 칠해져요.

## 설정
`Edit → Preferences → Add-ons → Maya Style UI`를 펼치면 다음을 바꿀 수 있어요.
- 키맵 적용 및 복원 버튼
- 마야 상단 바 켜기/끄기, 채널 박스를 속성 창에 표시
- Maya 워크스페이스 다시 만들기, 마야 색상 적용 및 블렌더 색상 복원
- 셸프 위치: Tool Header / Header / 숨김, 셸프 모양: 탭 / 드롭다운
- 우클릭 메뉴, 마킹 메뉴, 툴 설정 메뉴, 휠클릭 축 고정, 마야 단축키 켜기/끄기
- UV Editor 단축키(마킹 메뉴, 휠클릭, X/V 스냅) 켜기/끄기
- Input Line, 뷰포트 패널 메뉴, 옵션 박스, 선택 오브젝트 와이어프레임, 새 씬 기본값, 애니메이션 편집(탄젠트 버튼, 타임 슬라이더 메뉴) 켜기/끄기

## 설치할 때 "Permission denied" / "lock could not be created" 오류가 날 때
`C:\Program Files\Blender Foundation\Blender 5.0\portable\...` 같은 경로가 오류에 나오면, 블렌더가 설정과 확장을
쓰기 금지된 `Program Files` 안의 `portable` 폴더에 저장하려다 막힌 거예요. 애드온 문제가 아니라 블렌더 설치 위치 문제예요.

1. 블렌더를 끄고 `C:\Program Files\Blender Foundation\Blender 5.0` 을 엽니다.
2. `portable` 폴더 이름을 `portable_old` 로 바꿉니다 (관리자 권한 확인 → 계속).
3. 블렌더를 다시 켜면 설정이 `%APPDATA%\Blender Foundation\Blender\5.0` 에 저장돼요. 그다음 zip을 다시 설치하세요.

포터블 모드를 계속 쓰고 싶다면 블렌더 폴더를 `C:\Blender\` 처럼 쓰기 가능한 곳으로 옮겨서 실행해도 돼요.

## 셸프가 안 보일 때
뷰포트 헤더에서 `Blender → View → Tool Settings`를 체크하거나, 애드온 설정에서 **Show Shelf in All Viewports**를 누르세요.

## 직접 빌드
```
python build_zip.py   # dist/maya_style_v<버전>.zip 생성
```
버전을 올릴 때는 `maya_style/blender_manifest.toml`의 `version`과 `maya_style/__init__.py`의 `bl_info["version"]`을 같이 바꾸고 빌드하세요. 예전 zip은 지우지 않아요.
