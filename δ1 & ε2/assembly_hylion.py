"""Hylion v4 어셈블리 배치 스크립트
BHL(하체) + SO-ARM(팔) x2를 Hylion Assembly에 배치

v4 기준:
- BHL: 원점에 배치
- SO-ARM 좌: (0, +0.12, 0.82), rpy=(pi, 0, pi/2)
- SO-ARM 우: (0, -0.12, 0.82), rpy=(pi, 0, -pi/2)
"""
import os, hmac, hashlib, base64, time, uuid, json, math
import requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.environ['ONSHAPE_ACCESS_KEY']
SECRET_KEY = os.environ['ONSHAPE_SECRET_KEY']
BASE_URL = "https://cad.onshape.com"

HYLION = ("a741aa6d15d9e384d9ffa4d9", "2105b756950a92f6be143e8a", "0f1a46cb91bfc8ad1a11b7ea")
BHL    = ("bf0b8ec39be1c3ca659f6306", "560942befdcb6930ea4b7a28", "f015812d38473d4933b28001")  # 팔 suppress된 복사본
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
    if r.status_code >= 400:
        print(f"  Error: {r.text[:500]}")
    r.raise_for_status()
    if not r.text:
        return {}
    return r.json()


def get_assembly(did, wid, eid):
    path = f"/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}"
    r = requests.get(BASE_URL + path, headers=auth_headers("get", path))
    r.raise_for_status()
    return r.json()


def get_latest_version(did, wid):
    """가장 최신 유효 버전의 ID를 반환. 없으면 새로 생성."""
    r = requests.get(BASE_URL + f"/api/documents/{did}/versions",
                     headers=auth_headers("get", f"/api/documents/{did}/versions"))
    versions = r.json()
    # 뒤에서부터 탐색 (Onshape는 오래된순 반환, 마지막이 최신)
    # metadataWorkspaceId가 있는 버전만 유효
    for v in reversed(versions):
        if v.get("metadataWorkspaceId"):
            print(f"  버전 사용: {v.get('name', '?')} ({v['id'][:8]}...)")
            return v["id"]
    # 유효한 버전 없으면 새로 생성
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
    vid = get_latest_version(s_did, s_wid)
    path = f"/api/v9/assemblies/d/{t_did}/w/{t_wid}/e/{t_eid}/instances"
    time.sleep(2)
    post(path, {"documentId": s_did, "elementId": s_eid, "isAssembly": True, "versionId": vid})
    asm = get_assembly(t_did, t_wid, t_eid)
    instances = asm.get("rootAssembly", {}).get("instances", [])
    for inst in reversed(instances):
        if inst.get("documentId") == s_did and inst.get("elementId") == s_eid:
            return inst["id"]
    raise ValueError(f"삽입된 instance를 찾을 수 없음: {s_did}/{s_eid}")


def rpy_to_rotation_matrix(roll, pitch, yaw):
    """RPY (roll, pitch, yaw) → 3x3 회전 행렬
    순서: Z(yaw) → Y(pitch) → X(roll) — URDF 표준 순서
    """
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)

    R = [
        [cy*cp,  cy*sp*sr - sy*cr,  cy*sp*cr + sy*sr],
        [sy*cp,  sy*sp*sr + cy*cr,  sy*sp*cr - cy*sr],
        [-sp,    cp*sr,             cp*cr            ],
    ]
    return R


def set_transform(did, wid, eid, instance_id, tx=0, ty=0, tz=0, roll=0, pitch=0, yaw=0):
    """위치 + 회전(RPY)을 4x4 transform 행렬로 변환하여 적용"""
    R = rpy_to_rotation_matrix(roll, pitch, yaw)
    # Onshape 4x4 row-major: [R00, R01, R02, tx, R10, R11, R12, ty, R20, R21, R22, tz, 0, 0, 0, 1]
    transform = [
        R[0][0], R[0][1], R[0][2], tx,
        R[1][0], R[1][1], R[1][2], ty,
        R[2][0], R[2][1], R[2][2], tz,
        0, 0, 0, 1
    ]
    path = f"/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}/occurrencetransforms"
    post(path, {
        "isRelative": False,
        "occurrences": [{"path": [instance_id]}],
        "transform": transform
    })


if __name__ == "__main__":
    did, wid, eid = HYLION
    PI = math.pi

    # 1. 기존 instance 전부 삭제
    print("=" * 50)
    print("Hylion v4 어셈블리 배치")
    print("=" * 50)
    clear_all_instances(did, wid, eid)

    # 2. BHL 삽입 (원점)
    print("BHL 삽입...")
    bhl_id = insert(did, wid, eid, *BHL)
    set_transform(did, wid, eid, bhl_id, tx=0, ty=0, tz=0)
    print(f"  BHL instance: {bhl_id}\n")

    # 3. SO-ARM 좌측 삽입
    #    Onshape 좌표계: Z=위, X=오른쪽, Y=안쪽
    #    SO-ARM 원본은 위로 뻗는 구조 → 뒤집어야 함
    #    roll=PI(x축 180도)로 뒤집고, yaw로 좌우 방향 설정
    print("SO-ARM 좌측 삽입...")
    soarm_l = insert(did, wid, eid, *SOARM)
    set_transform(did, wid, eid, soarm_l,
                  tx=0.12, ty=0, tz=0.82,
                  roll=PI, pitch=PI, yaw=0)
    print(f"  SO-ARM L instance: {soarm_l}\n")

    # 4. SO-ARM 우측 삽입
    print("SO-ARM 우측 삽입...")
    soarm_r = insert(did, wid, eid, *SOARM)
    set_transform(did, wid, eid, soarm_r,
                  tx=-0.12, ty=0, tz=0.82,
                  roll=PI, pitch=PI, yaw=0)
    print(f"  SO-ARM R instance: {soarm_r}\n")

    print("=" * 50)
    print("완료! Onshape에서 결과를 확인하세요.")
    print("=" * 50)