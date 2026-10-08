# BlanderToMaya: Maya Style UI for Blender

블렌더를 마야처럼 쓰게 해 주는 애드온이에요. 설치하면 키맵, 셸프, 마킹 메뉴, 채널 박스가 한 번에 세팅돼요.

## 다운로드 및 설치

1. [`dist/maya_style.zip`](dist/maya_style.zip) 파일을 다운로드합니다. 파일을 연 뒤 **Download raw file** 버튼을 누르면 돼요. **압축은 풀지 마세요.**
2. 블렌더를 엽니다. **4.2 이상**을 지원해요.
3. `Edit → Preferences → Get Extensions` 화면에서 오른쪽 위 `⌄` 메뉴를 열고 **Install from Disk...**를 누른 뒤 zip을 선택합니다.
   (구버전 방식: `Add-ons` 탭 → `⌄` → **Install from Disk...**)
4. 설치되면 키맵이 자동으로 **Industry Compatible**(마야식)로 바뀌고, 뷰포트 상단에 셸프가 나타나요.

## 기능

### 1. 마야식 키맵
- 설치하는 순간 한 번 자동으로 적용돼요.
- Alt+좌클릭 회전, Alt+휠클릭 이동, Alt+우클릭 줌
- Q/W/E/R 선택·이동·회전·스케일, F 포커스
- **F8** 오브젝트/컴포넌트 전환, **F9** 버텍스, **F10** 엣지, **F11** 페이스
- 원래대로 돌리려면 Preferences의 애드온 설정에서 **Restore Blender Keymap**을 누르세요.

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

아이콘에 마우스를 올리면 설명이 나와요. 글자를 같이 보고 싶으면 설정에서 **Show Button Labels**를 켜세요.

### 3. 마킹 메뉴 (Shift+우클릭)
- **오브젝트 모드**: 기본 도형 생성, 아래쪽에 Smooth, Combine, Center Pivot, Freeze, Delete History 같은 버튼 묶음
- **에딧 모드**: Extrude, Bevel, Insert Edge Loop, Multi-Cut, Target Weld, Inset, Edge Slide, 아래쪽에 Bridge, Fill, Merge 같은 버튼 묶음

### 4. 채널 박스 (N 패널 → Channel Box 탭)
- Translate, Rotate, Scale, Visibility를 마야처럼 한 줄씩 보여줘요.
- SHAPES(메시 이름)와 INPUTS(모디파이어 = 마야의 히스토리)도 함께 보여줘요.
- **Layer Editor**: 컬렉션 숨기기와 렌더 토글, 선택한 오브젝트로 새 레이어 만들기

## 설정
`Edit → Preferences → Add-ons → Maya Style UI`를 펼치면 다음을 바꿀 수 있어요.
- 키맵 적용 및 복원 버튼
- 셸프 위치: Tool Header / Header / 숨김
- 마킹 메뉴, F8~F11 단축키 켜기/끄기

## 셸프가 안 보일 때
뷰포트 헤더에서 `View → Tool Settings`를 체크하거나, 애드온 설정에서 **Show Shelf in All Viewports**를 누르세요.

## 직접 빌드
```
python build_zip.py   # dist/maya_style.zip 생성
```
