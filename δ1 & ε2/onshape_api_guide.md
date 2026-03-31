# Onshape API 실전 가이드

> 이 문서는 `assembly_hylion.py` 개발 과정에서 직접 확인한 API 동작을 정리한 것입니다.
> 공식 문서: https://onshape-public.github.io/docs/api-adv/assemblies/
> API Explorer: https://cad.onshape.com/glassworks/explorer

---

## 인증 (API Key HMAC)

### 서명 문자열 형식

```
{method}\n{nonce}\n{date}\n{content-type}\n{path}\n{query}\n
```

- 전체 소문자로 변환 후 HMAC-SHA256 서명
- `path`와 `query`를 분리: path에는 query string 미포함, query는 별도 필드
- query string이 없으면 빈 문자열 (결과적으로 `\n\n`이 됨)
- query string이 있으면 `key=value&key=value` 형태로 포함
- GET 요청도 Content-Type을 `application/json`으로 고정

### Authorization 헤더

```
On {ACCESS_KEY}:HmacSHA256:{BASE64_SIGNATURE}
```

### Python 구현

```python
def auth_headers(method, path, body="", ctype="application/json"):
    nonce = uuid.uuid4().hex
    date  = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    msg   = f"{method}\n{nonce}\n{date}\n{ctype}\n{path}\n\n".lower()
    sig   = base64.b64encode(
        hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "Authorization": f"On {ACCESS_KEY}:HmacSHA256:{sig}",
        "Date": date,
        "On-Nonce": nonce,
        "Content-Type": ctype,
        "Accept": "application/json"
    }
```

---

## API 경로 규칙

### 현재 버전
- API Explorer 기준 현재 버전: `v14`
- 실제 동작 확인된 버전: `v9`
- 경로 형식: `/api/v9/{resource}/d/{did}/w/{wid}/e/{eid}`

### 동작 확인된 경로 형식

| 엔드포인트 | 경로 형식 |
|-----------|----------|
| 문서 조회 | `/api/documents/{did}` (버전 없이도 동작) |
| 문서 element 목록 | `/api/documents/{did}/elements` |
| 워크스페이스 목록 | `/api/documents/{did}/workspaces` |
| 버전 목록/생성 | `/api/documents/{did}/versions` |
| Assembly 인스턴스 삽입 | `/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}/instances` |
| Assembly Transform | `/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}/occurrencetransforms` |
| Assembly 정의 조회 | `/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}` |

> ⚠️ `/api/assemblies/{did}/...` (버전 없음, `/d/` 없음) → 404

---

## 주요 엔드포인트

### 1. createInstance — 어셈블리에 인스턴스 삽입

**POST** `/api/v9/assemblies/d/{targetDid}/w/{targetWid}/e/{targetEid}/instances`

**Request Body:**
```json
{
    "documentId": "{sourceDid}",
    "elementId": "{sourceEid}",
    "isAssembly": true,
    "versionId": "{sourceVersionId}"
}
```

**Response:** `{}` (빈 객체, 200 OK)

> ⚠️ 다른 문서에서 가져올 때 `versionId` 필수. 없으면 400 "Linked document references require a version identifier"
> ⚠️ `metadataWorkspaceId`가 null인 버전(STEP import 자동 생성 버전)은 사용 불가 → 새 버전 생성 필요

### 2. occurrencetransforms — Transform 적용

**POST** `/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}/occurrencetransforms`

**Request Body:**
```json
{
    "isRelative": false,
    "occurrences": [
        {
            "path": ["{instanceId}"]
        }
    ],
    "transform": [
        1, 0, 0, tx,
        0, 1, 0, ty,
        0, 0, 1, tz,
        0, 0, 0, 1
    ]
}
```

**Response:** `{}` (빈 객체, 200 OK)

> ⚠️ Transform 행렬: 번역(tx, ty, tz)은 **마지막 열**에 위치 (마지막 행 아님)
> ⚠️ 단위는 **미터(m)**

### 3. getAssemblyDefinition — 어셈블리 정의 조회

**GET** `/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}`

**Response 주요 필드:**
```json
{
    "rootAssembly": {
        "instances": [
            {
                "id": "{instanceId}",
                "documentId": "{sourceDid}",
                "elementId": "{sourceEid}",
                "name": "...",
                "type": "Assembly"
            }
        ]
    }
}
```

> createInstance 후 instance ID 조회에 사용 (createInstance가 ID를 반환하지 않으므로)

**Query Parameters (선택):**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `includeMateFeatures` | boolean | false | mate 정보 포함 |
| `includeMateConnectors` | boolean | false | mate connector 좌표 포함 |
| `includeNonSolids` | boolean | false | 비고체 포함 |
| `excludeSuppressed` | boolean | false | suppress된 항목 제외 |

> ⚠️ query parameter 사용 시 HMAC 서명의 query 필드에 포함 필요 (path와 분리)

---

## 버전 관리

### 버전 목록 조회

**GET** `/api/documents/{did}/versions`

**Response 주요 필드:**
```json
[
    {
        "id": "{versionId}",
        "metadataWorkspaceId": "{wsId 또는 null}",
        "type": "version"
    }
]
```

### 버전 생성

**POST** `/api/documents/{did}/versions`

**Request Body:**
```json
{
    "documentId": "{did}",
    "workspaceId": "{wid}",
    "name": "v1",
    "description": "initial"
}
```

> ⚠️ `metadataWorkspaceId`가 null인 버전은 크로스 문서 어셈블리 참조 불가
> → 정상 버전: "Copy workspace"로 복사한 문서에서 생성된 버전
> → 비정상 버전: STEP import 후 자동 생성된 버전

---

## 간섭 체크 (Interference Detection)

**POST** `/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}/interference`

배치 완료 후 부품끼리 겹치는지 자동 확인.
응답: 간섭이 발생한 파트 쌍 목록 + 간섭 볼륨

---

## 파트 치수 조회 (Mass Properties)

**GET** `/api/parts/{did}/{wid}/{eid}/{partid}/massproperties`

응답의 `periphery` 필드에서 bounding box 추출 → x/y/z 최대·최소값 → 내부 가용 공간 계산

| 조회 항목 | 용도 |
|-----------|------|
| 토르소 bounding box (x, y, z) | 내부 부품 배치 가능 영역 |
| 골반 bounding box | 배터리 A 슬롯 공간 확인 |
| base link 원점 위치 | 전체 Z 기준점 보정 |

---

## 인스턴스 삭제 (deleteInstance)

**DELETE** `/api/assemblies/d/{did}/w/{wid}/e/{eid}/instance/nodeid/{instanceId}`

중복 삽입된 instance 정리 시 사용. Body 불필요.

> ⚠️ 버전 prefix 없음 (`/api/v9/`가 아니라 `/api/`). 경로는 `instance/nodeid`.

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `GET /api/assemblies/{did}/...` → 404 | 경로 형식 오류 | `/api/v9/assemblies/d/{did}/...` 사용 |
| `GET /api/documents/{did}/w/{wid}/elements` → 404 | `/w/{wid}/` 포함 경로 비작동 | `/api/documents/{did}/elements` 사용 |
| `POST instances` → 400 "Linked document references require a version identifier" | versionId 누락 | 버전 생성 후 versionId 포함 |
| `POST instances` → 404 (두 번째 이후 삽입) | metadataWorkspaceId null인 버전 사용 | 유효한 버전 생성 후 사용 |
| `res["id"]` → KeyError | createInstance 응답이 `{}` | getAssemblyDefinition으로 instance ID 조회 |
| Transform 위치 어긋남 | tx/ty/tz를 마지막 행에 넣음 | 4x4 행렬 마지막 열 (열 인덱스 3)에 배치 |
