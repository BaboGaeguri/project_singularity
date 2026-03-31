# Onshape 어셈블리 환경 세팅 가이드

> 새 팀원이 Onshape API 기반 어셈블리 작업을 시작하기 위한 초기 세팅 문서
> API 레퍼런스 → `onshape_api_guide.md` | 작업 기록 → `hylion_assembly_worklog.md`

---

## 1. 원본 CAD 문서 확보

### BHL

원본 URDF(`berkeley_humanoid_lite/urdf/berkeley_humanoid_lite.urdf` 2번째 줄) 기반 문서:
```
https://cad.onshape.com/documents/fc6443b1d89dcba950e85b60
```

Documents 목록에서 우클릭 → **"Copy workspace..."** 로 내 계정에 복사

### SO-ARM 101

원본 URDF(`so-arm/so101_new_calib.urdf` 3번째 줄) 기반 문서:
```
https://cad.onshape.com/documents/7715cc284bb430fe6dab4ffd/w/4fd0791b683777b02f8d975a/e/826c553ede3b7592eb9ca800
```

view only 문서라 Copy workspace 불가 → 하단 툴바 **다운로드(`↓`)** → **Export as STEP** → 내 문서에 **Import → "Split into multiple documents"** 로 가져오기

---

## 2. Onshape API key 발급

1. `cad.onshape.com` → 우측 상단 프로필 아이콘 → **"My account"** → 좌측 **"Developer"** 탭
2. **"Create new API key"** 클릭
3. 이름: `project_singularity`
4. 권한 체크:
   - ✅ Application can read your profile information
   - ✅ Application can read your documents
   - ✅ Application can write to your documents
   - ✅ Application can delete your documents and workspaces
   - ☐ Application can request purchases on your behalf
   - ☐ Application can share and unshare documents on your behalf
5. **Access Key**와 **Secret Key** 저장 (Secret Key는 생성 시 한 번만 표시)

> ⚠️ 권한은 생성 후 수정 불가. 변경 필요 시 삭제 후 재발급.

프로젝트 루트에 `.env` 파일 생성 (`.gitignore`에 추가 필수):
```
ONSHAPE_ACCESS_KEY=발급받은_액세스키
ONSHAPE_SECRET_KEY=발급받은_시크릿키
```

---

## 3. Document ID 수집

Onshape 문서 URL 구조:
```
https://cad.onshape.com/documents/{did}/w/{wid}/e/{eid}
```

| 항목 | 설명 | URL 위치 |
|------|------|----------|
| `did` | Document ID | `/documents/` 뒤 |
| `wid` | Workspace ID | `/w/` 뒤 |
| `eid` | Element ID | `/e/` 뒤 |

**Element ID 확인 방법:** Onshape 하단 탭 우클릭 → "Copy tab URL" → URL 끝 `e/` 이후 문자열

현재 프로젝트 Document ID는 `hylion_assembly_worklog.md` 참조.

---

## 4. Python 환경 세팅

> ⚠️ **OS 참고:** Onshape API 설계 작업은 Windows/Ubuntu 모두 동일하게 동작.
> 로봇 구동(IsaacLab, ROS2) 작업은 Ubuntu 권장.

> CadQuery가 Python 3.12+ 미지원이라 **3.11** 사용. Onshape API 자체는 3.8+ 가능.

### Windows

Python 3.11.9 설치: `python.org` → Python 3.11.9 → **Windows installer (64-bit)**
- 이미 다른 Python 버전이 있으면 **"Add python.exe to PATH"는 체크하지 않음**
- `py -3.11`로 버전 지정 사용

```bash
py -3.11 -m venv .venv_design
.venv_design\Scripts\activate
pip install requests python-dotenv
```

### Ubuntu

```bash
python3.11 -m venv .venv_design
source .venv_design/bin/activate
pip install requests python-dotenv
```

활성화되면 터미널 앞에 `(.venv_design)` 표시됨.

---

## 5. 동작 확인

```bash
python "δ1 & ε2/inspect_assembly.py"
```

에러 없이 어셈블리 JSON이 `δ1 & ε2/onshape/assembly_dump.json`에 저장되면 세팅 완료.