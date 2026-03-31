"""Hylion 어셈블리 현재 상태 조회 스크립트"""
import os, hmac, hashlib, base64, time, uuid, json
import requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.environ['ONSHAPE_ACCESS_KEY']
SECRET_KEY = os.environ['ONSHAPE_SECRET_KEY']
BASE_URL = "https://cad.onshape.com"

HYLION = ("a741aa6d15d9e384d9ffa4d9", "2105b756950a92f6be143e8a", "0f1a46cb91bfc8ad1a11b7ea")

def auth_headers(method, path, ctype="application/json"):
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

def get_assembly(did, wid, eid):
    path = f"/api/v9/assemblies/d/{did}/w/{wid}/e/{eid}"
    r = requests.get(BASE_URL + path, headers=auth_headers("get", path))
    r.raise_for_status()
    return r.json()

def format_transform(matrix):
    """4x4 transform 행렬에서 위치(tx, ty, tz)와 회전 정보 추출"""
    if not matrix or len(matrix) < 16:
        return "N/A"
    # Onshape transform: row-major 4x4
    # [R00, R01, R02, tx,  R10, R11, R12, ty,  R20, R21, R22, tz,  0, 0, 0, 1]
    tx, ty, tz = matrix[3], matrix[7], matrix[11]
    # 회전 대각 성분 (단위행렬이면 회전 없음)
    r00, r11, r22 = matrix[0], matrix[5], matrix[10]
    rotation_info = "회전 없음(단위행렬)" if (abs(r00-1)<0.01 and abs(r11-1)<0.01 and abs(r22-1)<0.01) else f"회전 있음 diag=[{r00:.3f}, {r11:.3f}, {r22:.3f}]"
    return f"위치=({tx:.4f}, {ty:.4f}, {tz:.4f})m  |  {rotation_info}"

SOARM  = ("32d468d3a6994ea4b9d0cfa1", "4702c8115f56790e62e507c5", "61ca4b83d9996a40877b20fc")
BHL    = ("f0fecca5eed67c8c3b107deb", "5986bd9b41326a2034f55e3a", "8a738ee5d00bb7ca5f8b3bc0")

TARGETS = {"hylion": HYLION, "soarm": SOARM, "bhl": BHL}

if __name__ == "__main__":
    import sys
    target_name = sys.argv[1] if len(sys.argv) > 1 else "hylion"
    if target_name not in TARGETS:
        print(f"사용법: python inspect_assembly.py [{'|'.join(TARGETS.keys())}]")
        sys.exit(1)
    did, wid, eid = TARGETS[target_name]
    print(f"대상: {target_name}")
    print(f"어셈블리 조회 중: did={did}\n")

    asm = get_assembly(did, wid, eid)

    # 전체 JSON을 파일로 저장 (상세 분석용)
    out_path = os.path.join(os.path.dirname(__file__), "onshape", f"{target_name}_dump.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(asm, f, indent=2, ensure_ascii=False)
    print(f"전체 JSON → {out_path} 저장 완료\n")

    # rootAssembly 정보
    root = asm.get("rootAssembly", {})
    instances = root.get("instances", [])
    occurrences = root.get("occurrences", [])

    print(f"=== Instances ({len(instances)}개) ===")
    for i, inst in enumerate(instances):
        print(f"\n[{i}] name: {inst.get('name', '?')}")
        print(f"    id: {inst.get('id', '?')}")
        print(f"    type: {inst.get('type', '?')}")
        print(f"    documentId: {inst.get('documentId', '?')}")
        print(f"    elementId: {inst.get('elementId', '?')}")

    print(f"\n=== Occurrences ({len(occurrences)}개) ===")
    for i, occ in enumerate(occurrences):
        path_ids = occ.get("path", [])
        transform = occ.get("transform", [])
        fixed = occ.get("fixed", False)
        hidden = occ.get("hidden", False)
        print(f"\n[{i}] path: {path_ids}")
        print(f"    transform: {format_transform(transform)}")
        print(f"    fixed: {fixed}  |  hidden: {hidden}")

    # 서브어셈블리 정보
    sub_assemblies = asm.get("subAssemblies", [])
    if sub_assemblies:
        print(f"\n=== Sub-Assemblies ({len(sub_assemblies)}개) ===")
        for sa in sub_assemblies:
            print(f"  documentId: {sa.get('documentId', '?')}")
            print(f"  instances: {len(sa.get('instances', []))}개")

    print("\n조회 완료.")