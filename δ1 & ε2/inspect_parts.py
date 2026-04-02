"""Onshape 파트별 소재/질량/밀도 조회 스크립트"""
import os, hmac, hashlib, base64, time, uuid, json
import requests
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.environ['ONSHAPE_ACCESS_KEY']
SECRET_KEY = os.environ['ONSHAPE_SECRET_KEY']
BASE_URL = "https://cad.onshape.com"

# 문서 정보 (did, wid)
BHL    = ("f0fecca5eed67c8c3b107deb", "5986bd9b41326a2034f55e3a")
SOARM  = ("32d468d3a6994ea4b9d0cfa1", "4702c8115f56790e62e507c5")
HYLION = ("a741aa6d15d9e384d9ffa4d9", "2105b756950a92f6be143e8a")
SO100  = ("8c3443ad2476530f652d160f", "cbfc0795034ec0eb76266c9e")
SO100_COPY = ("777450bd9cf2ea12995524af", "21332a10decdb024c210faae")

TARGETS = {"bhl": BHL, "soarm": SOARM, "hylion": HYLION, "so100": SO100, "so100copy": SO100_COPY}


def auth_headers(method, path, query="", ctype="application/json"):
    nonce = uuid.uuid4().hex
    date  = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    msg   = f"{method}\n{nonce}\n{date}\n{ctype}\n{path}\n{query}\n".lower()
    sig   = base64.b64encode(
        hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "Authorization": f"On {ACCESS_KEY}:HmacSHA256:{sig}",
        "Date": date, "On-Nonce": nonce,
        "Content-Type": ctype, "Accept": "application/json"
    }


def get_parts(did, wid):
    """문서 내 모든 파트 목록 조회 (소재 포함)"""
    path = f"/api/v9/parts/d/{did}/w/{wid}"
    url = BASE_URL + path
    r = requests.get(url, headers=auth_headers("get", path))
    r.raise_for_status()
    return r.json()


def get_mass_properties(did, wid, eid, part_id):
    """특정 파트의 질량 속성 조회 (질량, 체적, 밀도, 무게중심, 관성 텐서)"""
    path = f"/api/v9/parts/d/{did}/w/{wid}/e/{eid}/partid/{part_id}/massproperties"
    url = BASE_URL + path
    r = requests.get(url, headers=auth_headers("get", path))
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    import sys

    target_name = sys.argv[1] if len(sys.argv) > 1 else "bhl"
    if target_name not in TARGETS:
        print(f"사용법: python inspect_parts.py [{'|'.join(TARGETS.keys())}]")
        sys.exit(1)

    did, wid = TARGETS[target_name]
    print(f"대상: {target_name}")
    print(f"파트 목록 조회 중: did={did}\n")

    parts = get_parts(did, wid)

    # 전체 JSON 저장
    out_path = os.path.join(os.path.dirname(__file__), "onshape", f"{target_name}_parts.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parts, f, indent=2, ensure_ascii=False)
    print(f"전체 JSON → {out_path} 저장 완료\n")

    # 파트별 요약 출력
    print(f"=== 파트 목록 ({len(parts)}개) ===\n")
    print(f"{'파트 이름':<40} {'소재':<25} {'elementId'}")
    print("-" * 100)

    for part in parts:
        name = part.get("name", "?")
        eid = part.get("elementId", "?")
        material = part.get("material", {})
        mat_name = material.get("displayName", "미지정") if material else "미지정"
        print(f"{name:<40} {mat_name:<25} {eid}")

    # --mass 옵션: 각 파트의 질량 속성도 조회
    if "--mass" in sys.argv:
        print(f"\n\n=== 질량 속성 조회 ===\n")
        print(f"{'파트 이름':<40} {'질량(kg)':<12} {'체적(m³)':<15} {'밀도(kg/m³)':<12} {'소재'}")
        print("-" * 110)

        mass_data = []
        for part in parts:
            name = part.get("name", "?")
            eid = part.get("elementId", "?")
            part_id = part.get("partId", "?")
            material = part.get("material", {})
            mat_name = material.get("displayName", "미지정") if material else "미지정"

            try:
                mp = get_mass_properties(did, wid, eid, part_id)
                bodies = mp.get("bodies", {})
                # 첫 번째 body의 mass properties
                for body_id, body in bodies.items():
                    mass = body.get("mass", [0])[0]
                    volume = body.get("volume", [0])[0]
                    density = mass / volume if volume > 0 else 0
                    print(f"{name:<40} {mass:<12.6f} {volume:<15.9f} {density:<12.1f} {mat_name}")
                    mass_data.append({
                        "name": name,
                        "elementId": eid,
                        "partId": part_id,
                        "material": mat_name,
                        "mass_kg": mass,
                        "volume_m3": volume,
                        "density_kg_m3": density
                    })
                    break
            except Exception as e:
                print(f"{name:<40} {'조회 실패':<12} {'':<15} {'':<12} {mat_name}  ({e})")

        # 질량 데이터 JSON 저장
        mass_path = os.path.join(os.path.dirname(__file__), "onshape", f"{target_name}_mass.json")
        with open(mass_path, "w", encoding="utf-8") as f:
            json.dump(mass_data, f, indent=2, ensure_ascii=False)
        print(f"\n질량 데이터 → {mass_path} 저장 완료")

        total_mass = sum(d["mass_kg"] for d in mass_data)
        print(f"\n총 질량: {total_mass:.3f} kg")

    print("\n조회 완료.")