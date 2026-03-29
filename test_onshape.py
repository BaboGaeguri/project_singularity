import os, hmac, hashlib, base64, time, uuid, json
import requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.environ['ONSHAPE_ACCESS_KEY']
SECRET_KEY = os.environ['ONSHAPE_SECRET_KEY']
BASE_URL = "https://cad.onshape.com"

HYLION_DID = "a741aa6d15d9e384d9ffa4d9"
HYLION_WID = "2105b756950a92f6be143e8a"
HYLION_EID = "0f1a46cb91bfc8ad1a11b7ea"

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

def get(path):
    r = requests.get(BASE_URL + path, headers=auth_headers("get", path))
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.text[:1000]}")
    return r

# 1. 인증 테스트: 내 계정 정보 조회
print("=== 1. 인증 테스트 (/api/users/sessioninfo) ===")
get("/api/users/sessioninfo")

# 2. 문서 존재 확인
print("\n=== 2. Hylion 문서 조회 ===")
get(f"/api/documents/{HYLION_DID}")

SOARM_DID = "32d468d3a6994ea4b9d0cfa1"
SOARM_WID = "4702c8115f56790e62e507c5"
SOARM_EID = "61ca4b83d9996a40877b20fc"

# 3. SOARM 문서 접근 확인
print("\n=== 3. SOARM 문서 조회 ===")
get(f"/api/documents/{SOARM_DID}")

# 4. SOARM element 목록
print("\n=== 4. SOARM element 목록 ===")
get(f"/api/documents/{SOARM_DID}/elements")
