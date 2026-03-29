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
    print(f"BHL: {bhl_id}")

    print("SO-ARM 좌측 삽입...")
    soarm_l = insert(did, wid, eid, *SOARM)
    set_transform(did, wid, eid, soarm_l, tx=0.15, ty=0.2, tz=0.75)
    print(f"SO-ARM L: {soarm_l}")

    print("SO-ARM 우측 삽입...")
    soarm_r = insert(did, wid, eid, *SOARM)
    set_transform(did, wid, eid, soarm_r, tx=0.15, ty=-0.2, tz=0.75)
    print(f"SO-ARM R: {soarm_r}")

    print("\n완료. Onshape에서 결과 확인 후 transform 값 보정하세요.")