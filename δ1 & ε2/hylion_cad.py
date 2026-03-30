"""
하이리온 로봇 CAD v3 — 외피 쉘 + 내부 부품 참조 블록
=======================================================
실행: python hylion_cad.py
출력: step_files/ 폴더

[색상 범례]
  회색       : 외피 쉘
  빨강/주황  : 배터리 A/B
  노랑       : 제어 보드 레이어 (PDB·DC-DC·BMS·U2D2 등)
  초록       : NUC BeeLink N95
  파랑       : Jetson Orin Nano Super
  보라       : XL430 목 서보 ×2
  하늘색     : OAK-D Lite 카메라
  검정       : 스피커
  주황       : MG90S 입 서보

[치수 근거]
  hyrion_dimensions.md + hyrion_parts_weight.md
  배터리 A: 135×42×49mm (6S 4000mAh LiPo)
  배터리 B: 93×57×23mm  (12V 4000mAh Li-ion)
  NUC     : 126×113×37mm
  Orin    : 100×79×21mm
  XL430   : 50×36×36mm ×2
  OAK-D Lite: 91×28×17mm ×2
"""

import cadquery as cq
import os

os.makedirs("step_files", exist_ok=True)
T = 3  # 외피 두께 (mm)


# ─────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────

def _xdir(normal):
    """normal과 평행하지 않은 xDir 반환"""
    return (0, 1, 0) if abs(normal[0]) > 0.9 else (1, 0, 0)

def cut_cyl(ox, oy, oz, r, depth, normal=(0, 1, 0)):
    return (
        cq.Workplane(cq.Plane(origin=(ox, oy, oz), xDir=_xdir(normal), normal=normal))
        .circle(r).extrude(depth)
    )

def cut_rect(ox, oy, oz, w, h, depth, normal=(0, 1, 0)):
    return (
        cq.Workplane(cq.Plane(origin=(ox, oy, oz), xDir=_xdir(normal), normal=normal))
        .rect(w, h).extrude(depth)
    )

def hollow(solid, w, d, h, z0=0, fillet=0):
    """상하단 모두 개방형 속 비우기
    fillet: 외피 수직 모서리 라운드 반경 → 내부 박스에 (fillet-T) 적용
            0이면 라운드 없음 (sharp corner, 외피가 fillet 없을 때)
    """
    inner = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(0, 0, z0))
        .box(w - 2*T, d - 2*T, h, centered=(True, True, False))
    )
    if fillet > T:
        inner = inner.edges("|Z").fillet(fillet - T)
    return solid.cut(inner)

def ref_box(cx, cy, cz, w, d, h):
    """내부 부품 참조 블록 — 중심점(cx,cy,cz) 기준, w=X폭, d=Y깊이, h=Z높이"""
    return (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(cx, cy, cz))
        .box(w, d, h, centered=(True, True, True))
    )

def ref_box_z0(cx, cy, z0, w, d, h):
    """내부 부품 참조 블록 — 하단 Z=z0 기준"""
    return ref_box(cx, cy, z0 + h / 2, w, d, h)


# ══════════════════════════════════════════════════════════════════════
# 1. 머리 (Head)
#
# 치수: 너비 220mm × 깊이 200mm × 높이 350mm  (hyrion_dimensions: 35cm)
#
# 내부 부품:
#   OAK-D Lite ×2 (91×28×17mm) — 눈/물체감지·거리측정, 좌우 ±55mm
#   MEMS 마이크 ×2              — 귀/목소리인식, 좌우 측면
#   소형 스피커 20mm ×1         — 입/말소리출력
#   PAM8403 앰프 (30×20×5mm)   — 스피커 증폭
#   MG90S 서보 (22×11×27mm)    — 입 개합
#   ※ XL430 목 서보 ×2 → 토르소 상단 배치 (머리 무게 미포함)
#
# 개구부:
#   정면 OAK-D Lite 창 ×2 (93×30mm)
#   정면 입 슬롯 (60×22mm, MG90S)
#   정면 스피커 그릴 (50×18mm)
#   측면 마이크 홀 ×2 (Ø8mm)
#   하단 목 소켓 (Ø90mm, XL430 배선 통과)
# ══════════════════════════════════════════════════════════════════════
print("머리 생성 중...")

WH, DH, HH = 220, 200, 350
RH      = 45     # 모서리 라운드 (캐릭터 느낌)
NECK_R  = 45     # 목 소켓 반경 (XL430 ×2 + 배선 공간)

# 외피 쉘 (하단 개방)
head_shell = (
    cq.Workplane("XY")
    .box(WH, DH, HH, centered=(True, True, False))
    .edges("|Z").fillet(RH)
    .faces("<Z").shell(-T)
)
# 목 소켓 홀 (Ø90mm)
head_shell = head_shell.cut(cut_cyl(0, 0, 0, NECK_R, T * 3, normal=(0, 0, -1)))

# OAK-D Lite 눈 개구부 ×2 (93×30mm, 정면, 높이 60%)
# 두 카메라 중심 간격 110mm (각 ±55mm)
for ex in [-55, 55]:
    head_shell = head_shell.cut(cut_rect(ex, -DH / 2, HH * 0.60, 93, 30, T * 4))

# MG90S 입 슬롯 (60×22mm, 정면, 높이 32%)
head_shell = head_shell.cut(cut_rect(0, -DH / 2, HH * 0.32, 60, 22, T * 4))

# 스피커 그릴 (50×18mm, 정면, 높이 22%)
head_shell = head_shell.cut(cut_rect(0, -DH / 2, HH * 0.22, 50, 18, T * 4))

# MEMS 마이크 홀 ×2 (Ø8mm, 좌우 측면, 높이 55%)
head_shell = head_shell.cut(cut_cyl(-WH / 2, 0, HH * 0.55, 4, T * 3, normal=(-1, 0, 0)))
head_shell = head_shell.cut(cut_cyl( WH / 2, 0, HH * 0.55, 4, T * 3, normal=( 1, 0, 0)))

# ── 내부 부품 참조 블록 ─────────────────────────────────────────────
# OAK-D Lite: 정면 안쪽 벽에 밀착 (Y = -DH/2 + T + 17/2)
oak_cy = -(DH / 2 - T - 8.5)
oak_l  = ref_box(-55, oak_cy, HH * 0.60, 91, 17, 28)   # 왼쪽 카메라
oak_r  = ref_box( 55, oak_cy, HH * 0.60, 91, 17, 28)   # 오른쪽 카메라

# MG90S 서보 (22×11×27mm): 입 슬롯 뒤쪽
mg90s  = ref_box(0, 0, HH * 0.32, 22, 27, 11)

# MEMS 마이크 (5×5×5mm): 측면 안쪽
mic_l  = ref_box(-(WH / 2 - T - 3), 0, HH * 0.55, 5, 5, 5)
mic_r  = ref_box( (WH / 2 - T - 3), 0, HH * 0.55, 5, 5, 5)

# 스피커 20mm (Ø20mm → 25×25×5mm 블록)
spk    = ref_box(0, -(DH / 2 - T - 3), HH * 0.22, 25, 5, 25)

# PAM8403 앰프 (30×20×5mm): 스피커 바로 뒤
pam    = ref_box(0, 0, HH * 0.12, 30, 20, 5)

head_assy = cq.Assembly()
head_assy.add(head_shell, name="head_shell",    color=cq.Color(0.85, 0.85, 0.90))
head_assy.add(oak_l,      name="OAK-D_left",    color=cq.Color(0.20, 0.60, 0.90))
head_assy.add(oak_r,      name="OAK-D_right",   color=cq.Color(0.20, 0.60, 0.90))
head_assy.add(mg90s,      name="MG90S_servo",   color=cq.Color(0.90, 0.50, 0.10))
head_assy.add(mic_l,      name="MEMS_mic_L",    color=cq.Color(0.50, 0.50, 0.50))
head_assy.add(mic_r,      name="MEMS_mic_R",    color=cq.Color(0.50, 0.50, 0.50))
head_assy.add(spk,        name="speaker_20mm",  color=cq.Color(0.10, 0.10, 0.10))
head_assy.add(pam,        name="PAM8403_amp",   color=cq.Color(0.20, 0.70, 0.20))
head_assy.save("step_files/hylion_head.step")
print("  ✓ hylion_head.step")


# ══════════════════════════════════════════════════════════════════════
# 2. 토르소 (Torso)
#
# 치수: 너비 185mm × 깊이 148mm × 높이 250mm  (hyrion_dimensions: 25cm)
# 너비 근거: NUC 126mm + 2020 알루미늄 프레임 20mm×2 + 여유 = 185mm
#
# 내부 3층 레이아웃 (아래→위, hyrion_dimensions.md):
#
#   Z   5~ 57: [3층] 배터리
#               배터리 A (135×42×49mm, 6S LiPo) — 왼쪽
#               배터리 B (93×57×23mm,  12V Li-ion) — 오른쪽
#
#   Z  59~ 94: [2층] 제어 보드
#               U2D2×2, ESP32, Waveshare, CAN-USB×2, IMU,
#               PDB, DC-DC×3, BMS×3, MOSFET, 비상정지 스위치, 40mm 팬
#
#   Z  96~133: [1층-A] NUC BeeLink N95 (126×113×37mm)
#   Z 135~156: [1층-B] Jetson Orin Nano Super (100×79×21mm)
#
#   Z 158~183: 케이블 여유 공간 (25mm)
#   Z 183~219: XL430 목 서보 ×2 (50×36×36mm, 나란히)
#   Z 220~250: 40mm 냉각 팬 마운트 위치
#
# 개구부:
#   상단 배기팬 홀 Ø42mm (Orin TDP 25W 대응)
#   하단 흡기 슬롯 ×4 (배터리 구역)
#   배면 NUC 포트 창 (80×35mm, USB·LAN 접근)
#   정면 상태 LED 창 (50×10mm)
#   측면 어깨 플랜지 ×2 (SO-ARM101 마운트)
# ══════════════════════════════════════════════════════════════════════
print("토르소 생성 중...")

WT, DT, HT = 185, 148, 250
RT = 15

# 내부 Z 기준점
Z_BAT   = 5     # 배터리 시작
Z_CTRL  = 59    # 제어 보드 시작 (5+49+shelf2+3)
Z_NUC   = 96    # NUC 시작      (59+35+shelf2)
Z_ORIN  = 135   # Orin 시작     (96+37+shelf2)
Z_CABLE = 158   # 케이블 공간   (135+21+shelf2)
Z_SERVO = 183   # XL430 시작    (158+25)
Z_FAN   = 220   # 팬 위치       (250-30)
NECK_R_T = 45

# 외피 쉘 (상하단 개방)
torso_shell = (
    cq.Workplane("XY")
    .box(WT, DT, HT, centered=(True, True, False))
    .edges("|Z").fillet(RT)
)
torso_shell = hollow(torso_shell, WT, DT, HT, fillet=RT)

# 목 보스 (상단 Ø90×30mm 빈 원통)
boss_o = cut_cyl(0, 0, HT, NECK_R_T,     30, normal=(0, 0, 1))
boss_i = cut_cyl(0, 0, HT, NECK_R_T - T, 30, normal=(0, 0, 1))
torso_shell = torso_shell.union(boss_o.cut(boss_i))

# 상단 배기팬 홀 (Ø42mm)
torso_shell = torso_shell.cut(cut_cyl(0, 0, HT, 21, T * 3, normal=(0, 0, 1)))

# 하단 흡기 슬롯 ×4 (배터리 구역 냉각)
for ox in [-55, -18, 18, 55]:
    torso_shell = torso_shell.cut(cut_rect(ox, 0, 0, 22, 10, T * 3, normal=(0, 0, -1)))

# 어깨 마운트 플랜지 ×2 (SO-ARM101, XL430 서보 구역 높이)
SH_Z, SH_H, SH_EXT = Z_SERVO, 50, 28
for sign in [-1, 1]:
    flange = (
        cq.Workplane(cq.Plane(
            origin=(sign * WT / 2, 0, SH_Z + SH_H / 2),
            xDir=(0, 1, 0), normal=(sign, 0, 0)
        ))
        .rect(DT * 0.65, SH_H).extrude(SH_EXT)
    )
    torso_shell = torso_shell.union(flange)
    for dy in [-DT * 0.18, DT * 0.18]:
        torso_shell = torso_shell.cut(
            cut_cyl(sign * (WT / 2 + SH_EXT), dy, SH_Z + SH_H / 2,
                    2.5, SH_EXT + T, normal=(-sign, 0, 0))
        )

# 배면 NUC 포트 개구부 (USB·LAN, Z_NUC 근처)
torso_shell = torso_shell.cut(cut_rect(0, DT / 2, Z_NUC + 18, 80, 35, T * 4, normal=(0, -1, 0)))

# 정면 상태 LED 창
torso_shell = torso_shell.cut(cut_rect(0, -DT / 2, Z_ORIN + 30, 50, 10, T * 4))

# ── 내부 부품 참조 블록 ─────────────────────────────────────────────
# [3층] 배터리 A (135×42×49mm) — X 왼쪽 배치
#   w=42(X폭), d=135(Y깊이), h=49(Z높이)
bat_a = ref_box_z0(-28, 0, Z_BAT, 42, 135, 49)

# [3층] 배터리 B (93×57×23mm) — X 오른쪽 배치
#   w=57(X폭), d=93(Y깊이), h=23(Z높이)
bat_b = ref_box_z0(22, 0, Z_BAT, 57, 93, 23)

# [2층] 제어 보드 레이어 통합 블록 (U2D2·PDB·DC-DC·BMS·ESP32·팬 등)
ctrl  = ref_box_z0(0, 0, Z_CTRL, WT - 20, DT - 20, 35)

# [1층-A] NUC BeeLink N95 (126×113×37mm)
nuc   = ref_box_z0(0, 0, Z_NUC, 126, 113, 37)

# [1층-B] Jetson Orin Nano Super (100×79×21mm)
orin  = ref_box_z0(0, 0, Z_ORIN, 100, 79, 21)

# XL430 목 서보 ×2 (50×36×36mm, 나란히)
xl430_l = ref_box_z0(-28, 0, Z_SERVO, 50, 36, 36)
xl430_r = ref_box_z0( 28, 0, Z_SERVO, 50, 36, 36)

# 40mm 냉각 팬 (40×40×10mm)
fan = ref_box_z0(0, 0, Z_FAN, 40, 40, 10)

torso_assy = cq.Assembly()
torso_assy.add(torso_shell, name="torso_shell",     color=cq.Color(0.85, 0.85, 0.90))
torso_assy.add(bat_a,       name="battery_A_6S",    color=cq.Color(0.90, 0.15, 0.15))
torso_assy.add(bat_b,       name="battery_B_12V",   color=cq.Color(0.90, 0.50, 0.10))
torso_assy.add(ctrl,        name="control_boards",  color=cq.Color(0.85, 0.80, 0.10))
torso_assy.add(nuc,         name="NUC_BeeLink_N95", color=cq.Color(0.15, 0.70, 0.20))
torso_assy.add(orin,        name="Jetson_Orin",     color=cq.Color(0.10, 0.35, 0.90))
torso_assy.add(xl430_l,     name="XL430_neck_L",    color=cq.Color(0.65, 0.10, 0.70))
torso_assy.add(xl430_r,     name="XL430_neck_R",    color=cq.Color(0.65, 0.10, 0.70))
torso_assy.add(fan,         name="cooling_fan_40mm",color=cq.Color(0.55, 0.55, 0.55))
torso_assy.save("step_files/hylion_torso.step")
print("  ✓ hylion_torso.step")


# ══════════════════════════════════════════════════════════════════════
# 3. 골반 (Pelvis)  — BHL URDF 실측값
#
# BHL URDF 확인값:
#   pelvis 박스: 150×140×230mm → 외피 +5mm = 155×145×235mm
#   힙 관절 간격: ±80mm
# ══════════════════════════════════════════════════════════════════════
print("골반 생성 중...")

WP, DP, HP = 155, 145, 235
HIP_OFF = 80

pelvis = (
    cq.Workplane("XY")
    .box(WP, DP, HP, centered=(True, True, False))
    .edges("|Z").fillet(12)
)
pelvis = hollow(pelvis, WP, DP, HP, fillet=12)

for hx in [-HIP_OFF, HIP_OFF]:
    pelvis = pelvis.cut(cut_cyl(hx, 0, 0, 35, T * 3, normal=(0, 0, -1)))

INSET = 20
for bx, by in [
    (-WP / 2 + INSET, -DP / 2 + INSET), ( WP / 2 - INSET, -DP / 2 + INSET),
    (-WP / 2 + INSET,  DP / 2 - INSET), ( WP / 2 - INSET,  DP / 2 - INSET),
]:
    pelvis = pelvis.cut(cut_cyl(bx, by, HP, 3, T * 3, normal=(0, 0, 1)))

pelvis_assy = cq.Assembly()
pelvis_assy.add(pelvis, name="pelvis_shell", color=cq.Color(0.85, 0.85, 0.90))
pelvis_assy.save("step_files/hylion_pelvis.step")
print("  ✓ hylion_pelvis.step")


# ══════════════════════════════════════════════════════════════════════
# 4. 단측 다리 (Leg)  — BHL URDF 실측값
#
# hyrion_dimensions.md URDF 기반:
#   허벅지 (골반~무릎): 150mm  (leg_left_knee_pitch_joint y=0.15m)
#   정강이 (무릎~발목): 160mm  (leg_left_ankle_pitch_joint y=0.16m)
#   발목~발:            50mm   (leg_left_ankle_roll_joint  y=0.05m)
#
# OnShape에서 미러링(YZ 평면) → 양쪽 다리
# ══════════════════════════════════════════════════════════════════════
print("다리(단측) 생성 중...")

G = 12  # 관절 갭

# ── 발 (Foot, 50mm) ───────────────────────────────────────────────────
WF, LF, HF = 110, 170, 50
foot = (
    cq.Workplane("XY")
    .box(WF, LF, HF, centered=(True, True, False))
    .edges("|Z").fillet(10)
    .edges("#Z").fillet(6)
    .faces(">Z").shell(-T)
)

# ── 정강이 (Lower Leg, 160mm) ────────────────────────────────────────
WL, DL, LL = 68, 60, 160
zL = HF + G   # 62mm

lower = (
    cq.Workplane("XY")
    .transformed(offset=cq.Vector(0, 0, zL))
    .box(WL, DL, LL, centered=(True, True, False))
    .edges("|Z").fillet(10)
)
lower = hollow(lower, WL, DL, LL, z0=zL, fillet=10)
lower = lower.cut(cut_cyl(0, 0, zL,      18, T * 3, normal=(0, 0, -1)))  # 발목 홀
lower = lower.cut(cut_cyl(0, 0, zL + LL, 20, T * 3, normal=(0, 0,  1)))  # 무릎 홀

# ── 허벅지 (Upper Leg, 150mm) ────────────────────────────────────────
WU, DU, LU = 78, 70, 150
zU = zL + LL + G   # 234mm

upper = (
    cq.Workplane("XY")
    .transformed(offset=cq.Vector(0, 0, zU))
    .box(WU, DU, LU, centered=(True, True, False))
    .edges("|Z").fillet(12)
)
upper = hollow(upper, WU, DU, LU, z0=zU, fillet=12)
upper = upper.cut(cut_cyl(0, 0, zU + LU, 23, T * 3, normal=(0, 0, 1)))  # 힙 홀

# ── 합치기 ───────────────────────────────────────────────────────────
leg = foot.union(lower).union(upper)
cq.exporters.export(leg, "step_files/hylion_leg.step")
print("  ✓ hylion_leg.step")


print("""
══════════════════════════════════════════════════
완료! step_files/ 폴더 확인하세요.

OnShape에서 볼 때:
  외피(회색) + 내부 부품 블록(색상별)이 함께 보임
  부품명은 파트 트리에서 확인 가능
  (battery_A_6S, NUC_BeeLink_N95, Jetson_Orin 등)
══════════════════════════════════════════════════
""")
