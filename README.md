# BlanderToMaya: Maya Style UI for Blender

블렌더를 마야처럼 쓰게 해 주는 애드온이에요. 설치하면 키맵, 셸프, 마킹 메뉴, 채널 박스가 한 번에 세팅돼요.

## 다운로드 및 설치

1. 최신 버전 [`dist/maya_style_v0.2.0.zip`](dist/maya_style_v0.2.0.zip)을 다운로드합니다. 파일을 연 뒤 **Download raw file** 버튼을 누르면 돼요. **압축은 풀지 마세요.**
   - 예전 버전은 [`dist/`](dist/) 폴더에, 버전별 변경 내용은 [CHANGELOG.md](CHANGELOG.md)에 있어요.
2. 블렌더를 엽니다. **4.2 이상**을 지원해요.
3. `Edit → Preferences → Get Extensions` 화면에서 오른쪽 위 `⌄` 메뉴를 열고 **Install from Disk...**를 누른 뒤 zip을 선택합니다.
   (구버전 방식: `Add-ons` 탭 → `⌄` → **Install from Disk...**)
4. 설치되면 키맵이 자동으로 **Industry Compatible**(마야식)로 바뀌고, 뷰포트 상단에 셸프가 나타나요.
5. 새 버전으로 업데이트할 때도 같은 방법으로 새 zip을 설치하면 이전 버전을 덮어써요.

## 기능

### 1. 마야식 단축키
설치하면 키맵이 한 번 자동으로 **Industry Compatible**로 바뀌고, 그 위에 마야 단축키를 덮어씌워요.

**화면 조작**
| 키 | 기능 |
|---|---|
| Alt + 좌클릭 드래그 | 회전 (Tumble) |
| Alt + 휠클릭 드래그 | 이동 (Track) |
| Alt + 우클릭 드래그 | 확대/축소 (Dolly) |
| F | 선택한 오브젝트를 화면 중앙에 |
| A | 전체 오브젝트를 화면 중앙에 |
| Space | 4분할 뷰 ↔ 단일 뷰 |
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
- 마킹 메뉴, 마야 단축키 켜기/끄기

## 셸프가 안 보일 때
뷰포트 헤더에서 `View → Tool Settings`를 체크하거나, 애드온 설정에서 **Show Shelf in All Viewports**를 누르세요.

## 직접 빌드
```
python build_zip.py   # dist/maya_style_v<버전>.zip 생성
```
버전을 올릴 때는 `maya_style/blender_manifest.toml`의 `version`과 `maya_style/__init__.py`의 `bl_info["version"]`을 같이 바꾸고 빌드하세요. 예전 zip은 지우지 않아요.
