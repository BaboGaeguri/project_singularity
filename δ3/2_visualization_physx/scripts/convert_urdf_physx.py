import argparse
import os

import omni.kit.commands
import omni.usd

def convert_urdf_to_usd(urdf_path, usd_path):
    """
    Converts a URDF file to a USD file with PhysX properties.
    """
    if not os.path.exists(urdf_path):
        raise FileNotFoundError(f"URDF file not found: {urdf_path}")

    # Isaac Sim 5.1 URDF importer uses command API.
    status, import_config = omni.kit.commands.execute("URDFCreateImportConfig")
    if not status:
        raise RuntimeError("Failed to create URDF import config")

    import_config.fix_base = False
    import_config.make_default_prim = True
    import_config.merge_fixed_joints = False
    import_config.convex_decomp = False
    import_config.import_inertia_tensor = True
    import_config.create_physics_scene = True

    status, prim_path = omni.kit.commands.execute(
        "URDFParseAndImportFile",
        urdf_path=urdf_path,
        import_config=import_config,
        dest_path=usd_path,
        get_articulation_root=True,
    )
    if not status:
        raise RuntimeError(f"Failed to import URDF from {urdf_path}")
    if not prim_path:
        raise RuntimeError(f"URDF importer returned empty prim path for {urdf_path}")

    # Save stage explicitly after import.
    omni.usd.get_context().save_as_stage(usd_path)
    print(f"Successfully imported URDF to {prim_path}")
    print(f"Saved USD file to {usd_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert URDF to USD for PhysX.")
    
    # Get the absolute path of the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Default URDF path relative to the script location
    default_urdf_path = os.path.join(script_dir, "../../../δ1 & ε2/urdf/hylion_v6.urdf")
    
    # Default USD path relative to the script location
    default_usd_path = os.path.join(script_dir, "../usd/hylion_v6_physx.usd")

    parser.add_argument("--urdf_path", type=str, default=default_urdf_path, help="Path to the input URDF file.")
    parser.add_argument("--usd_path", type=str, default=default_usd_path, help="Path to the output USD file.")
    
    args = parser.parse_args()

    # Normalize paths to be absolute
    urdf_path = os.path.abspath(args.urdf_path)
    usd_path = os.path.abspath(args.usd_path)

    print(f"Converting URDF: {urdf_path}")
    print(f"Output USD: {usd_path}")

    convert_urdf_to_usd(urdf_path, usd_path)
