"""BHL, SO-ARM 문서의 버전 목록 확인"""
import os, hmac, hashlib, base64, time, uuid, requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.environ['ONSHAPE_ACCESS_KEY']
SECRET_KEY = os.environ['ONSHAPE_SECRET_KEY']
BASE_URL = "https://cad.onshape.com"

BHL   = ("bf0b8ec39be1c3ca659f6306", "560942befdcb6930ea4b7a28")
SOARM = ("32d468d3a6994ea4b9d0cfa1", "4702c8115f56790e62e507c5")

def auth_headers(method, path):
    nonce = uuid.uuid4().hex
    date  = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    msg   = f"{method}\n{nonce}\n{date}\napplication/json\n{path}\n\n".lower()
    sig   = base64.b64encode(
        hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "Authorization": f"On {ACCESS_KEY}:HmacSHA256:{sig}",
        "Date": date, "On-Nonce": nonce,
        "Content-Type": "application/json", "Accept": "application/json"
    }

for name, (did, wid) in [("BHL (suppress)", BHL), ("SO-ARM", SOARM)]:
    path = f"/api/documents/{did}/versions"
    r = requests.get(BASE_URL + path, headers=auth_headers("get", path))
    versions = r.json()
    print(f"\n{name} — 버전 {len(versions)}개:")
    for v in versions:
        mid = v.get("metadataWorkspaceId", "None")
        print(f"  {v.get('name', '?'):<20} id={v['id'][:16]}...  metadataWid={str(mid)[:16]}")