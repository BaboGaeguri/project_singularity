"""Isaac Sim 5.1.0 에서 USD 파일을 GUI로 열기"""

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False, "renderer": "RayTracedLighting"})

import omni.usd
import omni.kit.app

USD_PATH = "/home/laba/project_singularity/δ3/usd/hylion_v3/hylion_v3.usda"

omni.usd.get_context().open_stage(USD_PATH)
print(f"[INFO] Opened: {USD_PATH}")

app = omni.kit.app.get_app_interface()
import contextlib
with contextlib.suppress(KeyboardInterrupt):
    while app.is_running():
        app.update()

simulation_app.close()
