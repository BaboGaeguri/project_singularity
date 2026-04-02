"""
URDF Visual Mesh Exporter
=========================
URDF 파일의 모든 visual mesh를 kinematic chain에 따라 배치하고
하나의 STL 파일로 합친 뒤, 전체 높이를 30cm로 축소하여 export합니다.

지원 geometry: mesh (STL), box, cylinder

사용법:
    python export_stl.py
"""

import os
import xml.etree.ElementTree as ET
from math import cos, sin
import numpy as np
import trimesh


# ─── 설정 ───────────────────────────────────────────────────────────
URDF_PATH = os.path.join(os.path.dirname(__file__), "urdf", "hylion_v6.urdf")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "urdf", "hylion_v6_30cm.stl")
TARGET_HEIGHT_M = 0.30  # 목표 높이 (meters)


# ─── RPY → 3x3 rotation matrix (URDF 표준: extrinsic X-Y-Z) ────────
def rpy_to_matrix(roll, pitch, yaw):
    cr, sr = cos(roll), sin(roll)
    cp, sp = cos(pitch), sin(pitch)
    cy, sy = cos(yaw), sin(yaw)
    return np.array([
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp,     cp * sr,                cp * cr               ],
    ])


# ─── origin xyz/rpy → 4x4 homogeneous transform ────────────────────
def origin_to_transform(origin_elem):
    """URDF <origin> 요소를 4x4 변환 행렬로 변환."""
    T = np.eye(4)
    if origin_elem is None:
        return T

    xyz_str = origin_elem.get("xyz", "0 0 0")
    rpy_str = origin_elem.get("rpy", "0 0 0")

    xyz = [float(v) for v in xyz_str.split()]
    rpy = [float(v) for v in rpy_str.split()]

    T[:3, :3] = rpy_to_matrix(rpy[0], rpy[1], rpy[2])
    T[:3, 3] = xyz
    return T


# ─── geometry → trimesh 객체 ────────────────────────────────────────
def geometry_to_mesh(geom_elem, urdf_dir):
    """URDF <geometry> 요소를 trimesh 객체로 변환."""
    mesh_elem = geom_elem.find("mesh")
    box_elem = geom_elem.find("box")
    cylinder_elem = geom_elem.find("cylinder")

    if mesh_elem is not None:
        filename = mesh_elem.get("filename")
        # 상대경로 → 절대경로 (URDF 파일 위치 기준)
        filepath = os.path.normpath(os.path.join(urdf_dir, filename))
        if not os.path.exists(filepath):
            print(f"  [WARNING] STL 파일 없음, 건너뜀: {filepath}")
            return None
        loaded = trimesh.load(filepath, force="mesh")
        # scale 속성 처리
        scale_str = mesh_elem.get("scale")
        if scale_str:
            scale = [float(v) for v in scale_str.split()]
            loaded.apply_scale(scale)
        return loaded

    elif box_elem is not None:
        size_str = box_elem.get("size")
        size = [float(v) for v in size_str.split()]
        return trimesh.creation.box(extents=size)

    elif cylinder_elem is not None:
        radius = float(cylinder_elem.get("radius"))
        length = float(cylinder_elem.get("length"))
        return trimesh.creation.cylinder(radius=radius, height=length)

    else:
        print(f"  [WARNING] 지원하지 않는 geometry 타입, 건너뜀")
        return None


# ─── kinematic tree 구축 ────────────────────────────────────────────
def build_kinematic_tree(root):
    """
    URDF의 joint 정보로 kinematic tree를 구축합니다.

    Returns:
        links: {name: link_element}
        joints: {name: joint_element}
        parent_to_children: {parent_link_name: [(joint_elem, child_link_name), ...]}
        root_link_name: str
    """
    links = {}
    joints = {}
    child_links = set()  # child로 등장하는 link 이름들

    for link_elem in root.findall("link"):
        links[link_elem.get("name")] = link_elem

    parent_to_children = {}

    for joint_elem in root.findall("joint"):
        joints[joint_elem.get("name")] = joint_elem
        parent_name = joint_elem.find("parent").get("link")
        child_name = joint_elem.find("child").get("link")
        child_links.add(child_name)

        if parent_name not in parent_to_children:
            parent_to_children[parent_name] = []
        parent_to_children[parent_name].append((joint_elem, child_name))

    # root link = parent에만 등장하고 child에는 없는 link
    all_link_names = set(links.keys())
    root_candidates = all_link_names - child_links
    if len(root_candidates) == 1:
        root_link_name = root_candidates.pop()
    else:
        # 여러 개면 "base"를 우선 선택
        root_link_name = "base" if "base" in root_candidates else root_candidates.pop()
        print(f"  [INFO] 여러 root 후보: {root_candidates}, '{root_link_name}' 선택")

    return links, joints, parent_to_children, root_link_name


# ─── link의 visual mesh들을 world transform 적용하여 수집 ───────────
def collect_visual_meshes(links, parent_to_children, root_link_name, urdf_dir):
    """
    BFS로 kinematic tree를 순회하며 각 link의 visual mesh를 수집합니다.
    각 mesh에 world transform(joint chain + visual origin)을 적용합니다.
    """
    meshes = []

    # BFS: (link_name, world_transform)
    queue = [(root_link_name, np.eye(4))]

    while queue:
        link_name, world_T = queue.pop(0)
        link_elem = links.get(link_name)

        if link_elem is not None:
            # 이 link의 모든 visual 처리
            for visual_elem in link_elem.findall("visual"):
                visual_origin = visual_elem.find("origin")
                visual_T = origin_to_transform(visual_origin)

                # mesh의 world transform = link world transform x visual origin transform
                mesh_world_T = world_T @ visual_T

                geom_elem = visual_elem.find("geometry")
                if geom_elem is not None:
                    mesh = geometry_to_mesh(geom_elem, urdf_dir)
                    if mesh is not None:
                        mesh.apply_transform(mesh_world_T)
                        meshes.append(mesh)

        # 자식 link들로 이동
        if link_name in parent_to_children:
            for joint_elem, child_name in parent_to_children[link_name]:
                joint_origin = joint_elem.find("origin")
                joint_T = origin_to_transform(joint_origin)

                # child의 world transform = parent의 world transform x joint transform
                child_world_T = world_T @ joint_T
                queue.append((child_name, child_world_T))

    return meshes


# ─── 메인 ──────────────────────────────────────────────────────────
def main():
    print(f"URDF 파일: {URDF_PATH}")
    print(f"출력 STL:  {OUTPUT_PATH}")
    print()

    # URDF 파싱
    tree = ET.parse(URDF_PATH)
    xml_root = tree.getroot()
    urdf_dir = os.path.dirname(os.path.abspath(URDF_PATH))

    # kinematic tree 구축
    links, joints, parent_to_children, root_link_name = build_kinematic_tree(xml_root)
    print(f"Root link: {root_link_name}")
    print(f"총 link 수: {len(links)}")
    print(f"총 joint 수: {len(joints)}")
    print()

    # visual mesh 수집 (world transform 적용)
    meshes = collect_visual_meshes(links, parent_to_children, root_link_name, urdf_dir)
    print(f"수집된 visual mesh 수: {len(meshes)}")

    if not meshes:
        print("[ERROR] visual mesh가 하나도 없습니다. 종료합니다.")
        return

    # 모든 mesh를 하나로 합치기
    combined = trimesh.util.concatenate(meshes)
    print(f"합친 mesh: vertices={len(combined.vertices)}, faces={len(combined.faces)}")

    # z 방향 크기 측정 및 축소
    z_min = combined.vertices[:, 2].min()
    z_max = combined.vertices[:, 2].max()
    original_height = z_max - z_min
    print(f"원본 높이: {original_height:.4f} m")

    scale_factor = TARGET_HEIGHT_M / original_height
    print(f"Scale factor: {scale_factor:.6f} ({TARGET_HEIGHT_M}m 목표)")

    # 균일 스케일링 적용
    combined.apply_scale(scale_factor)

    # 바닥을 z=0에 맞춤
    z_min_scaled = combined.vertices[:, 2].min()
    combined.apply_translation([0, 0, -z_min_scaled])

    final_height = combined.vertices[:, 2].max() - combined.vertices[:, 2].min()
    print(f"최종 높이: {final_height:.4f} m")

    # STL export
    combined.export(OUTPUT_PATH, file_type="stl")
    print(f"\nSTL 파일 저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()