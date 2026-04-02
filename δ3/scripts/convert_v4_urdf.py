"""Hylion URDF -> USD 변환기 (Isaac Sim 6.0.0 URDFImporter, Newton 학습용)."""

import argparse
import os

from isaacsim import SimulationApp


def parse_args():
    parser = argparse.ArgumentParser(description="Convert Hylion URDF to USD for Newton training")
    parser.add_argument(
        "--urdf",
        type=str,
        default="/home/laba/project_singularity/δ3/robot/hylion_v4.urdf",
        help="입력 URDF 경로",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="/home/laba/project_singularity/δ3/usd/hylion_v4",
        help="출력 USD 디렉토리",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    simulation_app = SimulationApp({"headless": True})

    from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig

    os.makedirs(args.out_dir, exist_ok=True)

    config = URDFImporterConfig(
        urdf_path=args.urdf,
        usd_path=args.out_dir,
        merge_mesh=False,
        collision_from_visuals=False,
        allow_self_collision=False,
    )

    importer = URDFImporter(config)
    result = importer.import_urdf()
    print(f"[OK] result: {result}")
    print(f"[OK] URDF: {args.urdf}")
    print(f"[OK] USD saved to: {args.out_dir}")

    simulation_app.close()


if __name__ == "__main__":
    main()
