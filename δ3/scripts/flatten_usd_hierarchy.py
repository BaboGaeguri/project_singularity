"""Flatten hylion v6 USD hierarchy to match BHL biped structure.

BHL biped USD:  /robot/base, /robot/leg_left_hip_roll, ...  (flat)
Hylion v6 USD:  /robot/Geometry/base/leg_left_hip_roll/...  (nested)

IsaacLab's contact sensor and PhysX tensor APIs expect flat hierarchy.
This script creates a new USD layer that re-parents rigid bodies to
the root level, matching BHL biped conventions.
"""

import sys
from pxr import Usd, UsdPhysics, Sdf, UsdGeom

input_path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/Users/admin/Desktop/project_singularity/δ3/usd/hylion_v6/hylion_v6/hylion_v6.usda"
output_path = sys.argv[2] if len(sys.argv) > 2 else input_path.replace(".usda", "_flat.usda")

# Open the composed stage (read-only)
stage = Usd.Stage.Open(input_path)
root_prim = stage.GetDefaultPrim()
root_name = root_prim.GetName()

print(f"Root prim: /{root_name}")

# Find all rigid bodies
rigid_bodies = []
frontier = [root_prim]
while frontier:
    p = frontier.pop(0)
    if p.HasAPI(UsdPhysics.RigidBodyAPI):
        rigid_bodies.append(p.GetPath().pathString)
        print(f"  Found rigid body: {p.GetPath()}")
    frontier.extend(p.GetChildren())

print(f"\nTotal rigid bodies: {len(rigid_bodies)}")

# Check current hierarchy depth
for rb in rigid_bodies:
    parts = rb.split("/")
    depth = len(parts) - 2  # subtract root and prim name
    name = parts[-1]
    if depth > 2:
        print(f"  NESTED ({depth} deep): {rb}")

print(f"\nBHL biped structure for reference:")
print(f"  /robot/base          (depth 1)")
print(f"  /robot/ankle_roll    (depth 1)")
print(f"\nHylion v6 structure:")
print(f"  /hylion/Geometry/base/.../.../ankle_roll  (depth 7)")
print(f"\nTo make IsaacLab contact sensor work, the USD needs to be regenerated")
print(f"with flat hierarchy from URDF, similar to how BHL's USD was created.")
print(f"\nThe URDF->USD converter that BHL uses produces flat structure.")
print(f"The converter used for hylion v6 produced nested structure.")
