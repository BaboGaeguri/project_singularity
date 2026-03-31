import os, hmac, hashlib, base64, time, uuid, json
import requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.environ['ONSHAPE_ACCESS_KEY']
SECRET_KEY = os.environ['ONSHAPE_SECRET_KEY']
BASE_URL = "https://cad.onshape.com"

HYLION = ("a741aa6d15d9e384d9ffa4d9", "2105b756950a92f6be143e8a", "0f1a46cb91bfc8ad1a11b7ea")
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
    print(f"  POST {path} → {r.status_code}")
    r.raise_for_status()
    if not r.text:
        return {}
    return r.json()

def get_assembly(did, wid, eid):
    path = f"/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}"
    r = requests.get(BASE_URL + path, headers=auth_headers("get", path))
    r.raise_for_status()
    return r.json()

def get_or_create_version(did, wid):
    r = requests.get(BASE_URL + f"/api/documents/{did}/versions",
                     headers=auth_headers("get", f"/api/documents/{did}/versions"))
    versions = r.json()
    for v in versions:
        if v.get("metadataWorkspaceId"):
            return v["id"]
    res = post(f"/api/documents/{did}/versions",
               {"documentId": did, "workspaceId": wid, "name": "v1", "description": "initial"})
    return res["id"]

def delete_instance(did, wid, eid, instance_id):
    path = f"/api/assemblies/d/{did}/w/{wid}/e/{eid}/instance/nodeid/{instance_id}"
    r = requests.delete(BASE_URL + path, headers=auth_headers("delete", path))
    print(f"  DELETE {instance_id} → {r.status_code}")
    r.raise_for_status()

def clear_all_instances(did, wid, eid):
    """기존 instance 전부 삭제"""
    asm = get_assembly(did, wid, eid)
    instances = asm.get("rootAssembly", {}).get("instances", [])
    if not instances:
        print("기존 instance 없음\n")
        return
    print(f"기존 instance {len(instances)}개 삭제 중...")
    for inst in instances:
        delete_instance(did, wid, eid, inst["id"])
        time.sleep(1)
    print()

def insert(t_did, t_wid, t_eid, s_did, s_wid, s_eid):
    vid = get_or_create_version(s_did, s_wid)
    path = f"/api/v9/assemblies/d/{t_did}/w/{t_wid}/e/{t_eid}/instances"
    time.sleep(2)
    post(path, {"documentId": s_did, "elementId": s_eid, "isAssembly": True, "versionId": vid})
    asm = get_assembly(t_did, t_wid, t_eid)
    instances = asm.get("rootAssembly", {}).get("instances", [])
    for inst in reversed(instances):
        if inst.get("documentId") == s_did and inst.get("elementId") == s_eid:
            return inst["id"]
    raise ValueError(f"삽입된 instance를 찾을 수 없음: {s_did}/{s_eid}")

def set_transform(did, wid, eid, instance_id, tx=0, ty=0, tz=0):
    path = f"/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}/occurrencetransforms"
    post(path, {
        "isRelative": False,
        "occurrences": [{"path": [instance_id]}],
        "transform": [1,0,0,tx, 0,1,0,ty, 0,0,1,tz, 0,0,0,1]
    })

if __name__ == "__main__":
    did, wid, eid = HYLION

    # 1. 기존 instance 전부 삭제
    clear_all_instances(did, wid, eid)

    # 2. BHL 삽입
    print("BHL 삽입...")
    bhl_id = insert(did, wid, eid, *BHL)
    set_transform(did, wid, eid, bhl_id, tz=0.0)
    print(f"BHL: {bhl_id}\n")

    # 3. SO-ARM 좌측 삽입
    print("SO-ARM 좌측 삽입...")
    soarm_l = insert(did, wid, eid, *SOARM)
    set_transform(did, wid, eid, soarm_l, tx=0.15, ty=0.2, tz=0.75)
    print(f"SO-ARM L: {soarm_l}\n")

    # 4. SO-ARM 우측 삽입
    print("SO-ARM 우측 삽입...")
    soarm_r = insert(did, wid, eid, *SOARM)
    set_transform(did, wid, eid, soarm_r, tx=0.15, ty=-0.2, tz=0.75)
    print(f"SO-ARM R: {soarm_r}\n")

    print("완료. Onshape에서 결과 확인 후 transform 값 보정하세요.")