"""
하이리온 내부 부품 배치 시각화
================================
몸통 (250 × 180 × 270mm) 및 머리 (200 × 100 × 180mm)의
내부 부품을 3D 박스로 표현하여 STEP 파일로 출력합니다.

좌표계:
  x : 0~250mm (정면에서 봤을 때 좌→우)
  y : 0~180mm (앞→뒤, 배→등)
  z : 0~270mm (아래→위, 다리쪽이 0)

실행:
  python "δ1 & ε2/hylion_internal_layout.py"

출력:
  δ1 & ε2/step_files/hylion_internal_layout.step
"""

import cadquery as cq
from cadquery import Assembly, Color
import os

# ───────────────────────────────────────
# 유틸: 코너 기준으로 박스 배치
# x0, y0, z0 = 박스의 좌·전·하단 코너
# ───────────────────────────────────────
def box_at(w, d, h, x0, y0, z0):
    return (
        cq.Workplane("XY")
        .box(w, d, h)
        .translate((x0 + w/2, y0 + d/2, z0 + h/2))
    )

asm = Assembly()

# ═══════════════════════════════════════════
# 몸통 외형 (참고용 반투명 박스)
# ═══════════════════════════════════════════
asm.add(
    box_at(250, 180, 270, 0, 0, 0),
    name="torso_outline",
    color=Color(0.8, 0.8, 0.8, 0.15)
)

# ═══════════════════════════════════════════
# 1층 — 배터리 (z: 0 ~ 65mm)
# ═══════════════════════════════════════════

# 8000mAh 배터리 (190×60×30mm) — 앞쪽 (y: 0~60)
asm.add(
    box_at(190, 60, 30, 30, 0, 17),
    name="battery_8000mAh",
    color=Color(0.27, 0.51, 0.71)   # steelblue
)

# SO-ARM 전용 배터리 (100×50×20mm) — 뒤쪽 (y: 60~110)
asm.add(
    box_at(100, 50, 20, 75, 62, 22),
    name="battery_soarm",
    color=Color(0.25, 0.41, 0.88)   # royalblue
)

# 층간 선반 1 (z: 65~67mm)
asm.add(
    box_at(250, 180, 2, 0, 0, 65),
    name="shelf_1",
    color=Color(0.75, 0.75, 0.75)
)

# ═══════════════════════════════════════════
# 2층 — 제어·전원 (z: 67 ~ 132mm)
# ═══════════════════════════════════════════
Z2 = 67
Z2_MID = 82

# BMS × 3 (60×40×20mm)
for i, x0 in enumerate([10, 80, 150]):
    asm.add(
        box_at(60, 40, 20, x0, 100, Z2_MID),
        name=f"BMS_{i+1}",
        color=Color(1.0, 0.55, 0.0)    # darkorange
    )

# DC-DC 벅컨버터 × 3 (50×25×15mm)
for i, x0 in enumerate([10, 70, 130]):
    asm.add(
        box_at(50, 25, 15, x0, 150, Z2_MID + 5),
        name=f"BuckConverter_{i+1}",
        color=Color(1.0, 0.84, 0.0)    # gold
    )

# PDB 전력분배보드 (80×60×10mm)
asm.add(
    box_at(80, 60, 10, 160, 90, Z2_MID),
    name="PDB",
    color=Color(0.13, 0.55, 0.13)   # forestgreen
)

# Waveshare Motor Control Board (43×27×15mm)
asm.add(
    box_at(43, 27, 15, 160, 155, Z2_MID),
    name="Waveshare_MCB",
    color=Color(0.24, 0.70, 0.44)   # mediumseagreen
)

# CAN-USB 어댑터 × 2 (40×25×10mm)
for i, x0 in enumerate([10, 60]):
    asm.add(
        box_at(40, 25, 10, x0, 30, Z2_MID + 5),
        name=f"CAN_USB_{i+1}",
        color=Color(0.58, 0.44, 0.86)   # mediumpurple
    )

# N-channel MOSFET (20×15×10mm)
asm.add(
    box_at(20, 15, 10, 120, 30, Z2_MID + 5),
    name="MOSFET",
    color=Color(1.0, 0.39, 0.28)    # tomato
)

# 전압/전류 센서 (30×20×10mm)
asm.add(
    box_at(30, 20, 10, 150, 30, Z2_MID + 5),
    name="voltage_current_sensor",
    color=Color(1.0, 0.50, 0.31)    # coral
)

# --- 벽면 수직 고정 부품 (x=0 측벽) ---

# U2D2 × 2 (48×18×14.6mm)
for i, y0 in enumerate([20, 60]):
    asm.add(
        box_at(14.6, 18, 48, 0, y0, Z2),
        name=f"U2D2_{i+1}",
        color=Color(0.70, 0.13, 0.13)   # firebrick
    )

# ESP32 DevKitC v4 (54.4×27.9×13mm)
asm.add(
    box_at(13, 27.9, 54.4, 0, 110, Z2),
    name="ESP32",
    color=Color(0.63, 0.32, 0.18)   # sienna
)

# MPU6050 IMU × 2 (21.2×16.4×3.3mm)
for i, y0 in enumerate([148, 164]):
    asm.add(
        box_at(3.3, 16.4, 21.2, 0, y0, Z2 + 20),
        name=f"IMU_{i+1}",
        color=Color(1.0, 0.41, 0.71)    # hotpink
    )

# 층간 선반 + 냉각 팬 (z: 132~144mm)
asm.add(
    box_at(250, 180, 2, 0, 0, 132),
    name="shelf_fan",
    color=Color(0.75, 0.75, 0.75)
)
asm.add(
    box_at(40, 40, 10, 105, 70, 134),
    name="cooling_fan",
    color=Color(0.53, 0.81, 0.98)   # lightskyblue
)

# ═══════════════════════════════════════════
# 3층 — 컴퓨팅 (z: 144 ~ 204mm)
# ═══════════════════════════════════════════
Z3 = 144

# Jetson Orin Nano Super (100×79×21mm)
asm.add(
    box_at(100, 79, 21, 10, 10, Z3 + 10),
    name="Jetson_Orin_Nano",
    color=Color(0.20, 0.80, 0.20)   # limegreen
)

# BeeLink N95 Mini PC (115×102×39mm)
asm.add(
    box_at(115, 102, 39, 120, 10, Z3 + 5),
    name="BeeLink_N95",
    color=Color(0.0, 0.39, 0.0)    # darkgreen
)

# 유전원 USB 3.0 허브 (50×30×20mm)
asm.add(
    box_at(50, 30, 20, 10, 140, Z3 + 5),
    name="USB_Hub",
    color=Color(0.44, 0.50, 0.56)   # slategray
)

# Ethernet 케이블 (배선 공간, 상징적 표시)
asm.add(
    box_at(100, 10, 5, 75, 165, Z3 + 5),
    name="Ethernet_cable",
    color=Color(1.0, 1.0, 0.0)     # yellow
)

# ═══════════════════════════════════════════
# 머리 (200 × 100 × 180mm)
# 몸통(270mm) + 목(40mm) 위에 배치
# ═══════════════════════════════════════════
H = 270 + 40
HX = 25

asm.add(
    box_at(200, 100, 180, HX, 40, H),
    name="head_outline",
    color=Color(0.8, 0.8, 0.8, 0.15)
)

# OAK-D Lite × 2 (91×28×17.5mm) — 눈
for i, x0 in enumerate([HX + 5, HX + 104]):
    asm.add(
        box_at(91, 28, 17.5, x0, 40, H + 145),
        name=f"OAK_D_Lite_{i+1}",
        color=Color(0.1, 0.1, 0.1)     # black
    )

# Dynamixel XL430 × 2 (28.5×46.5×34mm) — 목 관절
for i, x0 in enumerate([HX + 40, HX + 120]):
    asm.add(
        box_at(28.5, 46.5, 34, x0, 47, H + 80),
        name=f"XL430_{i+1}",
        color=Color(0.41, 0.41, 0.41)   # dimgray
    )

# MG90S 서보 (22.8×12.2×28.5mm) — 입
asm.add(
    box_at(22.8, 12.2, 28.5, HX + 60, 40, H + 20),
    name="MG90S_servo",
    color=Color(0.50, 0.50, 0.50)   # gray
)

# 소형 스피커 (30×20×5mm)
asm.add(
    box_at(30, 20, 5, HX + 100, 40, H + 25),
    name="speaker",
    color=Color(0.1, 0.1, 0.1)
)

# MEMS 마이크 × 2 (16.7×12.7×1.8mm) — 귀
asm.add(
    box_at(1.8, 12.7, 16.7, HX, 80, H + 80),
    name="MEMS_mic_L",
    color=Color(0.95, 0.95, 0.95)   # white
)
asm.add(
    box_at(1.8, 12.7, 16.7, HX + 198, 80, H + 80),
    name="MEMS_mic_R",
    color=Color(0.95, 0.95, 0.95)
)

# PAM8403 앰프 (21×18×3.4mm)
asm.add(
    box_at(21, 3.4, 18, HX + 85, 136, H + 80),
    name="PAM8403_amp",
    color=Color(0.94, 0.90, 0.55)   # khaki
)

# ═══════════════════════════════════════════
# STEP 파일 출력
# ═══════════════════════════════════════════
out_dir = os.path.join(os.path.dirname(__file__), "step_files")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "hylion_internal_layout.step")

asm.save(out_path)
print(f"저장 완료: {out_path}")
print()
print("다음 단계:")
print("  1. Onshape -> New Document -> Import -> 위 STEP 파일 선택")
print("  2. 각 박스가 부품을 나타냄 (이름으로 구분 가능)")
print("  3. Transform 값 보정 후 실제 CAD 모델로 교체")
