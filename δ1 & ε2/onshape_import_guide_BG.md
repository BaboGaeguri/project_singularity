# Onshape API 어셈블리 가이드 — BHL + SO-ARM 실제 도면 기반

> BHL, SO-ARM 원본 Onshape 문서를 Onshape API로 불러와
> 실제 치수 기반의 최종 로봇 어셈블리를 코드로 구성하는 방법

---

## 전체 플로우

```
[1] BHL / SO-ARM 원본 Onshape 문서 → 내 계정으로 복사   ✅ 완료
[2] Onshape API key 발급                                 ✅ 완료
[3] 어셈블리 문서 URL 및 document ID 수집                ✅ 완료
[4] Python 스크립트로 각 서브어셈블리 insert + Transform 배치
[5] Assembly JSON export → 검토 후 보정
```

---

## Step 1. 원본 CAD 문서 확보 ✅

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

## Step 2. Onshape API key 발급 ✅

1. `cad.onshape.com` → 우측 상단 프로필 아이콘 → **"My account"** → 좌측 **"Developer"** 탭
2. **"Create new API key"** 클릭
3. 이름: `project_sigularity`
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
ONSHAPE_ACCESS_KEY=on_XZ3Y7EJY7y9f6JAiVK4Oa
ONSHAPE_SECRET_KEY=발급받은_시크릿키
```

---

## Step 3. Document ID 수집 ✅

| 문서 | did | wid | eid |
|------|-----|-----|-----|
| **Hylion Assembly** (작업 문서) | `a741aa6d15d9e384d9ffa4d9` | `2105b756950a92f6be143e8a` | `bff9221de0592d13a616f0f2` |
| **BHL 복사본** | `f0fecca5eed67c8c3b107deb` | `5986bd9b41326a2034f55e3a` | `8a738ee5d00bb7ca5f8b3bc0` |
| **SO-ARM 복사본** | `32d468d3a6994ea4b9d0cfa1` | `4702c8115f56790e62e507c5` | `61ca4b83d9996a40877b20fc` |

**Element ID 확인 방법:** Onshape 하단 탭 우클릭 → "Copy tab URL" → URL 끝 `e/` 이후 문자열

---

## Step 4. Python 환경 세팅

> ⚠️ **OS 참고:** Onshape API 설계 작업은 Windows/Ubuntu 모두 동일하게 동작.
> 로봇 구동(IsaacLab, ROS2) 작업은 Ubuntu 권장.

### 4-1. Python 3.11.9 설치

`python.org` → Python 3.11.9 → **Windows installer (64-bit)** 다운로드
- 설치 첫 화면에서 **"Add python.exe to PATH"** 반드시 체크 후 **Install Now**

> **Add python.exe to PATH란?**
> 터미널에서 `python` 명령어를 어디서든 인식하게 해주는 설정.
> 체크 안 하면 `'python'은 인식되지 않는 명령어` 오류 발생.

> **여러 Python 버전이 설치된 경우:**
> Windows py 런처로 버전 지정 가능: `py -3.11`, `py -3.10` 등
> 가상환경 생성 시 버전이 환경에 고정되므로 혼용 걱정 없음.

설치 확인:
```bash
py -3.11 --version  # Python 3.11.9
```

> CadQuery가 Python 3.12+ 미지원이라 3.11 필수.
> Onshape API 스크립트 자체는 3.8+ 아무거나 가능하나 3.11로 통일.

### 4-2. 가상환경 생성 및 패키지 설치

**Windows:**
```bash
py -3.11 -m venv .venv_design
.venv_design\Scripts\activate
pip install -r requirements.txt -r requirements_design.txt
```

**Ubuntu:**
```bash
python3.11 -m venv .venv_design
source .venv_design/bin/activate
pip install -r requirements.txt -r requirements_design.txt
```

활성화되면 터미널 앞에 `(.venv_design)` 표시됨.

---

## Step 5. 어셈블리 배치 스크립트

프로젝트 루트에 `assemble_hylion.py` 파일을 생성하고 아래 내용을 작성:

```python
import os, hmac, hashlib, base64, time, uuid, json
import requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.environ['ONSHAPE_ACCESS_KEY']
SECRET_KEY = os.environ['ONSHAPE_SECRET_KEY']
BASE_URL = "https://cad.onshape.com"

HYLION = ("a741aa6d15d9e384d9ffa4d9", "2105b756950a92f6be143e8a", "bff9221de0592d13a616f0f2")
BHL    = ("f0fecca5eed67c8c3b107deb", "5986bd9b41326a2034f55e3a", "8a738ee5d00bb7ca5f8b3bc0")
SOARM  = ("32d468d3a6994ea4b9d0cfa1", "4702c8115f56790e62e507c5", "61ca4b83d9996a40877b20fc")

def auth_headers(method, path, body="", ctype="application/json"):
    nonce = uuid.uuid4().hex
    date  = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    msg   = f"{method}\n{nonce}\n{date}\n{ctype}\n{path}\n\n".lower()
    sig   = base64.b64encode(
        hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "Authorization": f"On {ACCESS_KEY}:HmacSHA256:{sig}",
        "Date": date, "On-Nonce": nonce,
        "Content-Type": ctype, "Accept": "application/json"
    }

def post(path, body):
    b = json.dumps(body)
    r = requests.post(BASE_URL + path, headers=auth_headers("post", path, b), data=b)
    r.raise_for_status()
    return r.json()

def insert(t_did, t_wid, t_eid, s_did, s_wid, s_eid):
    path = f"/api/assemblies/{t_did}/w/{t_wid}/e/{t_eid}/instances"
    res  = post(path, {"type":"Assembly","documentId":s_did,"workspaceId":s_wid,"elementId":s_eid})
    return res["id"]

def set_transform(did, wid, eid, instance_id, tx=0, ty=0, tz=0):
    path = f"/api/assemblies/{did}/w/{wid}/e/{eid}/occurrences/transforms"
    post(path, {
        "occurrences": [{"path": [instance_id]}],
        "transform": [1,0,0,0, 0,1,0,0, 0,0,1,0, tx,ty,tz,1],
        "isRelative": False
    })

if __name__ == "__main__":
    did, wid, eid = HYLION

    print("BHL 삽입...")
    bhl_id = insert(did, wid, eid, *BHL)
    set_transform(did, wid, eid, bhl_id, tz=0.0)  # BHL 원점 기준, 이후 보정
    print(f"BHL instance ID: {bhl_id}")

    print("SO-ARM 좌측 삽입...")
    soarm_l = insert(did, wid, eid, *SOARM)
    set_transform(did, wid, eid, soarm_l, tx=0.15, ty=0.2, tz=0.75)
    print(f"SO-ARM L instance ID: {soarm_l}")

    print("SO-ARM 우측 삽입...")
    soarm_r = insert(did, wid, eid, *SOARM)
    set_transform(did, wid, eid, soarm_r, tx=0.15, ty=-0.2, tz=0.75)
    print(f"SO-ARM R instance ID: {soarm_r}")

    print("\n완료. Onshape에서 결과 확인 후 transform 값 보정하세요.")
```

실행:
```bash
python assemble_hylion.py
```

**배치 기준 치수 (지면 Z=0 기준):**

| 파트 | 지면 기준 Z | 근거 |
|------|------------|------|
| 다리 (BHL) | 0 ~ 360mm | URDF joint offset 합산 |
| 골반 | 360 ~ 595mm | hyrion_dimensions.md |
| 토르소 1층 (Jetson + NUC) | 595 ~ 634mm | 39mm |
| 토르소 2층 (제어 보드류) | 636 ~ 671mm | 35mm |
| 토르소 3층 (배터리 A+B) | 673 ~ 730mm | 57mm |
| 목 (XL430) | 845 ~ 885mm | 서보 크기 기준 |
| 머리 | 885 ~ 1235mm | 설계 결정값 |
| SO-ARM 좌 | tx=0.15, ty=+0.2, tz=0.75 | 초기값, 보정 필요 |
| SO-ARM 우 | tx=0.15, ty=-0.2, tz=0.75 | 초기값, 보정 필요 |

---

## Step 6. BHL 토르소 내부 치수 자동 조회

수동 측정 없이 BHL 토르소 파트의 bounding box를 API로 추출한다.

```
GET /api/parts/{did}/{wid}/{eid}/{partid}/massproperties
→ 응답의 periphery 필드에서 bounding box 추출
→ x/y/z 최대·최소값 → 내부 가용 공간 계산
```

| 조회 항목 | 용도 |
|-----------|------|
| 토르소 bounding box (x, y, z) | 내부 부품 배치 가능 영역 |
| 골반 bounding box | 배터리 A 슬롯 공간 확인 |
| base link 원점 위치 | 전체 Z 기준점 보정 |

---

## Step 7. 간섭 체크 (Interference Detection)

배치 완료 후 부품끼리 겹치는지 자동으로 확인.

```
POST /api/assemblies/{did}/{wid}/{eid}/interference
→ 응답: 간섭이 발생한 파트 쌍 목록 + 간섭 볼륨
```

**워크플로우:**
```
스크립트 실행 → 간섭 체크 API 호출 → 간섭 파트 쌍 확인
    → 치수 수정 or 오프셋 조정 → 스크립트 재실행 → 반복
```

---

## Step 8. 배치 확정 후 검토

**API로 현재 상태 조회:**
```
GET https://cad.onshape.com/api/assemblies/{did}/{wid}/{eid}
```
→ 모든 instance, transform, mate 정보 JSON 반환 → AI 검토 요청 가능

**Onshape UI에서 export:**
- `File → Export → STEP` : 전체 어셈블리를 정확한 형상으로 export
- onshape-to-robot 재실행: Assembly → URDF 변환 → IsaacLab 시뮬레이션 연동

---

## 트러블슈팅

### API 인증 오류 (401)
- Access Key / Secret Key 오타 확인
- `.env` 파일이 스크립트 실행 경로와 같은 위치에 있는지 확인
- API key 만료 여부 확인 (`cad.onshape.com` → My account → Developer)

### Transform 배치 후 파트 위치가 어긋날 때
- URDF와 Onshape API 모두 미터(m) 단위로 동일
- 서브어셈블리 내부 원점 위치에 따라 오프셋 보정 필요
- Assembly JSON export 후 instance별 transform 값 확인하여 보정

### 간섭 체크 결과가 비어 있을 때
- 파트가 실제로 겹치지 않는 경우이거나 아직 배치되지 않은 경우
- Assembly에 instance가 정상적으로 insert됐는지 먼저 확인

### SO-ARM import 시 파트가 분리되어 보일 때
- STEP export → "Split into multiple documents"로 import한 경우 서브어셈블리가 별도 문서로 분리됨
- Assembly insert 시 최상위 Assembly element ID를 사용하면 전체가 하나로 삽입됨