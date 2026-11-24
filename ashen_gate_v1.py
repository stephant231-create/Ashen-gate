"""
ASHEN GATE — оригинальный псевдо-3D fantasy-FPS на Pygame.
Установка: python -m pip install pygame
Запуск:   python ashen_gate.py

Управление:
  W/S — вперёд/назад
  A/D — движение в стороны
  ←/→ или мышь — поворот
  ЛКМ или ПРОБЕЛ — выстрел; 1 — пистолет; 2 — двустволка; R — перезарядка
  E — открыть выход (если найдена ключ-карта)
  ESC — выход
"""

import math
import random
import sys
import pygame

pygame.init()

WIDTH, HEIGHT = 960, 600
HALF_H = HEIGHT // 2
FPS = 60
FOV = math.radians(66)
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH // 2
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 22
PROJ_COEFF = (WIDTH / 2) / math.tan(HALF_FOV)
SCALE = WIDTH // NUM_RAYS

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ASHEN GATE")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22, bold=True)
small_font = pygame.font.SysFont("consolas", 16)
big_font = pygame.font.SysFont("consolas", 52, bold=True)


LEVEL_ENEMY_COUNTS = [4, 5, 6, 8]
LEVEL_NAMES = ["Пепельный двор", "Багровые катакомбы",
               "Зал запутанных коридоров"]

MAPS = [
[
"1111111111111111",
"1000000000000001",
"1011100111011101",
"1000100000010001",
"1000101111010001",
"1000001000010001",
"1110001000010111",
"1000000000000001",
"1011011101110101",
"1001000000010001",
"1001001100010001",
"1000000000000001",
"1111111111111111",
],
[
"1111111111111111",
"1000000000000001",
"1011101110111101",
"1000100000100001",
"1110101100101101",
"1000000100000001",
"1011100101110101",
"1000000000010001",
"1010111101011101",
"1000100000000001",
"1000101110110101",
"1000000000000001",
"1111111111111111",
],
[
"1111111111111111",
"1000000000000001",
"1011101101110101",
"1000000000010001",
"1110110101011101",
"1000100001000001",
"1010101101110101",
"1000100000000001",
"1011101110101101",
"1000000010000001",
"1010111010110101",
"1000000000000001",
"1111111111111111",
],
[
"1111111111111111",
"1000000000000001",
"1011011101110101",
"1001000000010001",
"1001011101011101",
"1000000100000001",
"1110100101110101",
"1000000000010001",
"1011101101011101",
"1000100000000001",
"1010111011101101",
"1000000000000001",
"1111111111111111",
],
]


PALETTES = [
    ((78, 42, 39), (170, 75, 48), (235, 125, 65)),
    ((78, 24, 35), (160, 42, 55), (245, 90, 70)),
    ((55, 38, 66), (125, 65, 115), (205, 120, 180)),
    ((42, 28, 30), (125, 82, 48), (240, 180, 85)),
]

level = 0
floor_index = 0
world = MAPS[0]
map_h, map_w = len(world), len(world[0])
player_x, player_y = 1.7, 1.7
player_angle = 0.0
health = 100
ammo = 40
score = 0
has_key = False
shot_flash = 0.0
weapon_kick = 0.0
weapon_type = "pistol"
shotgun_owned = False
shotgun_loaded = 0
reload_timer = 0.0
reload_stage = 0
weapon_anim = 0.0
message = "Найди ключ-карту и доберись до выхода."
message_timer = 4.0
game_over = False
game_won = False
level_complete = False
exit_pos = (14.2, 11.2)
key_pos = (13.2, 1.7)
enemies = []
pickups = []
level_time = 0.0

def is_wall(x, y):
    ix, iy = int(x), int(y)
    return iy < 0 or iy >= map_h or ix < 0 or ix >= map_w or world[iy][ix] == "1"

def random_floor_position(used, min_distance=2.7, spacing=1.45):
    """Ищет свободное место, не ставя врагов и предметы вплотную друг к другу."""
    for _ in range(3000):
        x = random.uniform(1.3, map_w - 1.3)
        y = random.uniform(1.3, map_h - 1.3)
        if is_wall(x, y):
            continue
        if math.hypot(x-player_x, y-player_y) < min_distance:
            continue
        if math.hypot(x-key_pos[0], y-key_pos[1]) < 1.3:
            continue
        if math.hypot(x-exit_pos[0], y-exit_pos[1]) < 1.5:
            continue
        if any(math.hypot(x-a, y-b) < spacing for a, b in used):
            continue
        return x, y
    
    for yy in range(1, map_h-1):
        for xx in range(1, map_w-1):
            if not is_wall(xx+0.5, yy+0.5) and (xx, yy) not in used:
                return xx+0.5, yy+0.5
    return 2.5, 2.5

def setup_level(index, floor=0):
    global level, floor_index, world, map_h, map_w, player_x, player_y, player_angle
    global has_key, key_pos, exit_pos, enemies, pickups, level_time, message, message_timer, weapon_type, shotgun_owned, shotgun_loaded, reload_timer, reload_stage, weapon_anim
    level = index
    floor_index = floor

    map_index = 0 if level == 0 else (1 if level == 1 and floor_index == 0 else
                                      2 if level == 1 else 3)
    world = MAPS[map_index]
    map_h, map_w = len(world), len(world[0])
    player_x, player_y = 1.7, 1.7
    player_angle = 0.0
    has_key = False
    weapon_type = "shotgun" if shotgun_owned else "pistol"
    reload_timer = 0.0
    reload_stage = 0
    weapon_anim = 0.0
    
    exit_pos = (map_w-1.8, map_h-1.8)
    key_candidates = [(x+0.5, y+0.5) for y in range(1, map_h-1)
                      for x in range(1, map_w-1)
                      if not is_wall(x+0.5, y+0.5)
                      and math.hypot(x+0.5-player_x, y+0.5-player_y) > 5
                      and math.hypot(x+0.5-exit_pos[0], y+0.5-exit_pos[1]) > 3]
    key_pos = random.choice(key_candidates) if key_candidates else (map_w-2.5, 1.5)
    enemies = []
    used = [(player_x, player_y), key_pos, exit_pos]
    if level == 0:
        count = LEVEL_ENEMY_COUNTS[0]
    elif level == 1:
        count = LEVEL_ENEMY_COUNTS[1] if floor_index == 0 else LEVEL_ENEMY_COUNTS[2]
    else:
        count = LEVEL_ENEMY_COUNTS[3]
    for i in range(count):
        ex, ey = random_floor_position(used, min_distance=2.7, spacing=1.55)
        used.append((ex, ey))
        enemies.append({
            "x": ex, "y": ey, "hp": 2 if level < 2 else 3,
            "cooldown": random.uniform(1.0, 2.0),
            "phase": random.random()*6.28,
            "speed": 0.25 + level*0.045,
            "attack_flash": 0.0,
            "phase": random.random()*6.28
        })

    
    pickups = []
    pickup_specs = [("health", 20), ("health", 20),
                    ("ammo", 8), ("ammo", 8)]
    if level >= 1 and not shotgun_owned:
        pickup_specs.append(("shotgun", 0))
    for kind, amount in pickup_specs:
        px, py = random_floor_position(used, min_distance=2.0, spacing=1.15)
        used.append((px, py))
        pickups.append({"x": px, "y": py, "kind": kind, "amount": amount,
                        "phase": random.random()*6.28})

    level_time = 0.0
    message = "Найди ключ-карту и доберись до выхода."
    message_timer = 3.5

def cast_ray(angle):
    """Быстрый DDA-рейкастинг: проверяем пересечения границ клеток карты."""
    ray_dx = math.cos(angle)
    ray_dy = math.sin(angle)
    map_x, map_y = int(player_x), int(player_y)

    delta_x = abs(1.0 / ray_dx) if abs(ray_dx) > 1e-9 else 1e30
    delta_y = abs(1.0 / ray_dy) if abs(ray_dy) > 1e-9 else 1e30

    if ray_dx < 0:
        step_x = -1
        side_x = (player_x - map_x) * delta_x
    else:
        step_x = 1
        side_x = (map_x + 1.0 - player_x) * delta_x

    if ray_dy < 0:
        step_y = -1
        side_y = (player_y - map_y) * delta_y
    else:
        step_y = 1
        side_y = (map_y + 1.0 - player_y) * delta_y

    side = 0
    depth = 0.0
    while depth < MAX_DEPTH:
        if side_x < side_y:
            depth = side_x
            side_x += delta_x
            map_x += step_x
            side = 0
        else:
            depth = side_y
            side_y += delta_y
            map_y += step_y
            side = 1

        if map_y < 0 or map_y >= map_h or map_x < 0 or map_x >= map_w:
            break
        if world[map_y][map_x] == "1":
            hit_x = player_x + ray_dx * depth
            hit_y = player_y + ray_dy * depth
            corrected = max(0.01, depth * math.cos(angle - player_angle))
            shade = 0.72 if side == 0 else 1.0
            return corrected, shade, hit_x % 1, hit_y % 1

    return MAX_DEPTH, 1.0, 0.0, 0.0

def line_of_sight(x1, y1, x2, y2):
    distance = math.hypot(x2-x1, y2-y1)
    steps = max(1, int(distance*14))
    for i in range(1, steps):
        t = i/steps
        if is_wall(x1+(x2-x1)*t, y1+(y2-y1)*t):
            return False
    return True

def draw_world():
    wall_dark, wall_mid, glow = PALETTES[level]
    screen.fill((15, 8, 13))
    
    for y in range(HALF_H):
        k = y/HALF_H
        col = (int(28-12*k), int(13-5*k), int(22-6*k))
        pygame.draw.line(screen, col, (0, y), (WIDTH, y))
    
    pygame.draw.rect(screen, (34, 17, 20), (0, HALF_H, WIDTH, HALF_H))
    for i in range(1, 12):
        y = HALF_H + int((i/12)**2 * HALF_H)
        pygame.draw.line(screen, (75, 30, 26), (0, y), (WIDTH, y), 1)
    z_buffer = []
    ray_angle = player_angle-HALF_FOV
    for ray in range(NUM_RAYS):
        depth, shade, fx, fy = cast_ray(ray_angle)
        z_buffer.append(depth)
        wall_h = min(HEIGHT*2, int(PROJ_COEFF/depth))
        x = ray*SCALE
        y = HALF_H-wall_h//2
        fog = max(0.13, 1-depth/MAX_DEPTH)
        #
        variation = 0.83 + 0.17*math.sin((fx*7 + fy*5)*math.pi)
        base = [int(c*fog*shade*variation) for c in wall_mid]
        pygame.draw.rect(screen, tuple(max(0,min(255,c)) for c in base),
                         (x, y, SCALE+1, wall_h))
        if ray % 18 == 0:
            pygame.draw.line(screen, tuple(int(c*fog) for c in glow),
                             (x, y), (x, y+wall_h), 2)
        
        if ray % 8 == 0:
            pygame.draw.line(screen, tuple(int(c*0.65) for c in wall_dark),
                             (x, y+wall_h//3), (x+SCALE, y+wall_h//3), 1)
        ray_angle += DELTA_ANGLE
    return z_buffer

def project(x, y):
    dx, dy = x-player_x, y-player_y
    dist = math.hypot(dx, dy)
    angle = (math.atan2(dy, dx)-player_angle+math.pi)%(2*math.pi)-math.pi
    if dist < 0.1 or abs(angle) > HALF_FOV+0.25:
        return None
    sx = WIDTH/2 + math.tan(angle)*PROJ_COEFF
    size = min(HEIGHT, int(PROJ_COEFF/dist*0.68))
    return sx, size, dist, angle

def draw_demon(enemy, z_buffer):
    """Вооружённый мертвец в приземлённой, почти реалистичной манере старых FPS."""
    p = project(enemy["x"], enemy["y"])
    if not p:
        return
    sx, size, dist, angle = p
    idx = int(sx/SCALE)
    if not (0 <= idx < len(z_buffer)) or dist > z_buffer[idx]+0.2:
        return
    cx = int(sx)
    bob = math.sin(pygame.time.get_ticks()*0.003+enemy["phase"])*size*0.008
    cy = int(HALF_H+bob)
    r = max(8, size//3)
    
    shadow=(10,9,9); uniform=(48,48,42); uniform_light=(67,65,55)
    skin=(91,91,77); skin_light=(119,113,91); dark=(22,22,21)
    pygame.draw.ellipse(screen, shadow, (cx-r,cy+r//2,r*2,int(r*.62)))
   
    pygame.draw.polygon(screen,(35,35,32),[(cx-r//2,cy+r//5),(cx-r//8,cy+r//5),(cx-r//5,cy+r),(cx-r*3//4,cy+r)])
    pygame.draw.polygon(screen,(35,35,32),[(cx+r//8,cy+r//5),(cx+r//2,cy+r//5),(cx+r*3//4,cy+r),(cx+r//4,cy+r)])
    pygame.draw.ellipse(screen,(18,18,17),(cx-r*3//4,cy+r*3//4,r//2,max(3,r//5)))
    pygame.draw.ellipse(screen,(18,18,17),(cx+r//4,cy+r*3//4,r//2,max(3,r//5)))
    
    torso=[(cx-r,cy-r//2),(cx-r*4//5,cy-r),(cx+r*4//5,cy-r),(cx+r,cy-r//2),(cx+r*2//3,cy+r//2),(cx-r*2//3,cy+r//2)]
    pygame.draw.polygon(screen,uniform,torso)
    pygame.draw.polygon(screen,uniform_light,[(cx-r*4//5,cy-r),(cx-r//4,cy-r*3//4),(cx-r//3,cy+r//2),(cx-r*2//3,cy+r//2)])
    pygame.draw.line(screen,(28,29,27),(cx,cy-r*3//4),(cx,cy+r//3),max(1,r//15))
    
    pygame.draw.line(screen,(30,29,25),(cx-r//2,cy-r//2),(cx+r//2,cy+r//3),max(2,r//12))
    for side in (-1,1):
        pygame.draw.rect(screen,(34,34,29),(cx+side*r//2-r//9,cy-r//5,r//4,r//3),border_radius=2)
        pygame.draw.line(screen,(86,79,62),(cx+side*r//2-r//9,cy-r//5),(cx+side*r//2+r//9,cy-r//5),1)
    
    head_y=cy-r-int(r*.48)
    pygame.draw.rect(screen,(68,67,57),(cx-r//5,head_y+r//2,r//2,max(3,r//3)))
    pygame.draw.ellipse(screen,skin,(cx-r//2,head_y-r//2,r,max(7,int(r*1.18))))
    pygame.draw.arc(screen,(53,52,45),(cx-r//2,head_y-r//2,r,int(r*1.18)),3.3,6.1,max(1,r//13))
    
    pygame.draw.ellipse(screen,(34,32,29),(cx-r//3,head_y-r//10,max(2,r//5),max(2,r//8)))
    pygame.draw.ellipse(screen,(34,32,29),(cx+r//8,head_y-r//10,max(2,r//5),max(2,r//8)))
    pygame.draw.line(screen,(62,55,46),(cx,head_y),(cx-r//12,head_y+r//5),max(1,r//14))
    pygame.draw.line(screen,(49,43,39),(cx-r//5,head_y+r//3),(cx+r//5,head_y+r//3),max(1,r//14))
    
    armw=max(3,r//5)
    pygame.draw.line(screen,uniform_light,(cx-r*3//4,cy-r//2),(cx-r//5,cy-r//12),armw)
    pygame.draw.line(screen,uniform,(cx+r*3//4,cy-r//2),(cx+r//4,cy-r//12),armw)
    pygame.draw.circle(screen,skin,(cx-r//5,cy-r//12),max(2,r//9))
    pygame.draw.circle(screen,skin,(cx+r//4,cy-r//12),max(2,r//9))
    gy=cy-r//8
    
    pygame.draw.polygon(screen,(28,27,24),[(cx-r,gy-r//10),(cx-r//2,gy-r//8),(cx+r//2,gy-r//8),(cx+r,gy-r//10),(cx+r,gy+r//12),(cx-r,gy+r//12)])
    pygame.draw.rect(screen,(57,54,46),(cx-r//3,gy-r//7,max(4,r//2),max(3,r//4)))
    pygame.draw.line(screen,(17,18,17),(cx+r//3,gy-r//14),(cx+r*5//4,gy-r//14),max(2,r//12))
    pygame.draw.polygon(screen,(27,26,23),[(cx-r//5,gy+r//10),(cx+r//8,gy+r//10),(cx+r//5,gy+r//2),(cx-r//8,gy+r//2)])
    pygame.draw.line(screen,(100,88,67),(cx-r*3//4,gy),(cx-r//2,gy),1)
    if enemy.get("attack_flash",0)>0:
        pygame.draw.polygon(screen,(230,177,95),[(cx+r*5//4,gy-r//5),(cx+r*3//2,gy),(cx+r*5//4,gy+r//5)])

def draw_key_and_exit(z_buffer):
    
    if not has_key:
        p = project(*key_pos)
        if p:
            sx, size, dist, _ = p
            idx = int(sx/SCALE)
            if 0 <= idx < len(z_buffer) and dist < z_buffer[idx]:
                cy = int(HALF_H + math.sin(pygame.time.get_ticks()*0.004)*5)
                r = max(6, min(30, size//5))
                pygame.draw.polygon(screen, (45, 210, 190),
                                    [(int(sx),cy-r),(int(sx)+r,cy),
                                     (int(sx),cy+r),(int(sx)-r,cy)])
                pygame.draw.polygon(screen, (200, 255, 225),
                                    [(int(sx),cy-r),(int(sx)+r,cy),
                                     (int(sx),cy+r),(int(sx)-r,cy)], 2)
                pygame.draw.circle(screen, (25, 70, 80), (int(sx),cy), max(2,r//3))
    
    p = project(*exit_pos)
    if p:
        sx, size, dist, _ = p
        idx = int(sx/SCALE)
        if 0 <= idx < len(z_buffer) and dist < z_buffer[idx]+0.4:
            w = max(8, size//2)
            h = min(HEIGHT, size)
            rect = pygame.Rect(int(sx)-w//2, HALF_H-h//2, w, h)
            pygame.draw.rect(screen, (52, 24, 28), rect)
            pygame.draw.rect(screen, (185, 92, 58) if has_key else (100, 55, 58), rect, max(2,size//30))
            pygame.draw.line(screen, (245, 165, 90), (rect.centerx,rect.top+8),
                             (rect.centerx,rect.bottom-8), max(1,size//50))
            if has_key:
                pygame.draw.circle(screen, (100,255,190), (rect.centerx,rect.centery), max(3,size//18))


def draw_supply_pickups(z_buffer):
    for item in pickups:
        p = project(item["x"], item["y"])
        if not p:
            continue
        sx, size, dist, _ = p
        idx = int(sx / SCALE)
        if not (0 <= idx < len(z_buffer)) or dist >= z_buffer[idx]:
            continue
        bob = math.sin(pygame.time.get_ticks()*0.004 + item["phase"]) * 4
        cx, cy = int(sx), int(HALF_H + bob)
        r = max(5, min(19, size // 7))
        if item["kind"] == "health":
            # Красный знак аптечки
            pygame.draw.rect(screen, (115, 28, 35), (cx-r, cy-r, r*2, r*2), border_radius=3)
            pygame.draw.rect(screen, (255, 225, 205), (cx-r//3, cy-r+2, max(3, 2*r//3), 2*r-4))
            pygame.draw.rect(screen, (255, 225, 205), (cx-r+2, cy-r//3, 2*r-4, max(3, 2*r//3)))
            pygame.draw.rect(screen, (245, 120, 100), (cx-r, cy-r, r*2, r*2), 1, border_radius=3)
        elif item["kind"] == "shotgun":
            # Подбираемый громобой — заметная лежащая модель двустволки
            pygame.draw.rect(screen, (65, 39, 34), (cx-r*2, cy-r//3, r*4, max(4,r//2)), border_radius=3)
            pygame.draw.rect(screen, (190, 130, 78), (cx-r*2, cy-r//3, r*4, max(3,r//5)), 1, border_radius=3)
            pygame.draw.line(screen, (35, 28, 30), (cx-r,cy-r//2), (cx+r*2,cy-r//2), max(2,r//5))
            pygame.draw.line(screen, (35, 28, 30), (cx-r,cy+r//2), (cx+r*2,cy+r//2), max(2,r//5))
        else:
            # Золотистая пачка патронов
            rect = pygame.Rect(cx-r, cy-r//2, r*2, r)
            pygame.draw.rect(screen, (105, 65, 28), rect, border_radius=3)
            pygame.draw.rect(screen, (255, 205, 95), rect, 2, border_radius=3)
            for k in (-1, 0, 1):
                pygame.draw.line(screen, (255, 235, 160),
                                 (cx+k*r//2, cy-r//2+2), (cx+k*r//2, cy+r//2-2), 2)


def shoot():
    global ammo, shot_flash, weapon_kick, message, message_timer, score, shotgun_loaded, weapon_anim
    if reload_timer > 0:
        return
    if weapon_type == "shotgun" and shotgun_loaded <= 0:
        message, message_timer = "Нажми R, чтобы перезарядить", 1.0
        return
    if weapon_type == "pistol" and ammo <= 0:
        message, message_timer = "Нет зарядов!", 1.0
        return

    if weapon_type == "shotgun":
        shotgun_loaded -= 1
    else:
        ammo -= 1
    shot_flash = 0.18 if weapon_type == "shotgun" else 0.13
    weapon_kick = 1.0
    weapon_anim = 0.18
    target = None
    best = 999
    spread = 0.105 if weapon_type == "shotgun" else 0.025
    max_range = 5.8 if weapon_type == "shotgun" else 14.0
    for enemy in enemies:
        if enemy["hp"] <= 0:
            continue
        p = project(enemy["x"], enemy["y"])
        if not p:
            continue
        sx, size, dist, angle = p
        if abs(math.atan2(math.sin(angle), math.cos(angle))) < spread and dist < max_range and dist < best:
            if line_of_sight(player_x, player_y, enemy["x"], enemy["y"]):
                target, best = enemy, dist
    if target:
        target["hp"] -= 2 if weapon_type == "shotgun" else 1
        if target["hp"] <= 0:
            score += 100
    message_timer = 0

def start_reload():
    global reload_timer, reload_stage
    if weapon_type != "shotgun" or reload_timer > 0 or shotgun_loaded >= 2 or ammo <= 0:
        return
    reload_timer = 1.35
    reload_stage = 1

def draw_weapon():
    """Оружие и руки в первом лице: сталь, воронение и тёмное дерево."""
    t = reload_timer
    if t > 0:
        elapsed = 1.35-t
        if elapsed < 0.35:
            reload_offset = int(88 * elapsed/0.35)
        elif elapsed < 0.95:
            reload_offset = 88
        else:
            reload_offset = int(88 * (1-(elapsed-0.95)/0.40))
    else:
        reload_offset = 0
    kick = weapon_kick
    walk_bob = math.sin(pygame.time.get_ticks()*0.009)*2
    lift = int(kick*(22 if weapon_type=="shotgun" else 14)) + reload_offset + int(walk_bob)
    base_y = HEIGHT-118+lift
    
    pygame.draw.polygon(screen,(31,34,32),[(WIDTH//2-145,HEIGHT),(WIDTH//2-112,base_y+45),(WIDTH//2-55,base_y+65),(WIDTH//2-42,HEIGHT)])
    pygame.draw.polygon(screen,(31,34,32),[(WIDTH//2+145,HEIGHT),(WIDTH//2+112,base_y+45),(WIDTH//2+55,base_y+65),(WIDTH//2+42,HEIGHT)])
    pygame.draw.polygon(screen,(83,76,62),[(WIDTH//2-105,HEIGHT),(WIDTH//2-91,base_y+58),(WIDTH//2-56,base_y+70),(WIDTH//2-38,HEIGHT)])
    pygame.draw.polygon(screen,(83,76,62),[(WIDTH//2+105,HEIGHT),(WIDTH//2+91,base_y+58),(WIDTH//2+56,base_y+70),(WIDTH//2+38,HEIGHT)])
    pygame.draw.line(screen,(45,43,37),(WIDTH//2-91,base_y+65),(WIDTH//2-48,base_y+78),11)
    pygame.draw.line(screen,(45,43,37),(WIDTH//2+91,base_y+65),(WIDTH//2+48,base_y+78),11)
    if weapon_type=="shotgun":
       
        pygame.draw.polygon(screen,(34,29,24),[(WIDTH//2-72,HEIGHT),(WIDTH//2-52,base_y+25),(WIDTH//2+52,base_y+25),(WIDTH//2+72,HEIGHT)])
        pygame.draw.polygon(screen,(83,55,36),[(WIDTH//2-47,base_y+13),(WIDTH//2+47,base_y+13),(WIDTH//2+40,base_y+99),(WIDTH//2-40,base_y+99)])
        pygame.draw.line(screen,(125,85,53),(WIDTH//2-39,base_y+25),(WIDTH//2+39,base_y+25),3)
        pygame.draw.line(screen,(47,34,26),(WIDTH//2-35,base_y+83),(WIDTH//2+35,base_y+83),3)
        
        for off in (-17,17):
            pygame.draw.rect(screen,(20,22,22),(WIDTH//2+off-8,base_y-42,16,72),border_radius=3)
            pygame.draw.rect(screen,(73,76,73),(WIDTH//2+off-6,base_y-41,12,68),border_radius=2)
            pygame.draw.line(screen,(142,143,132),(WIDTH//2+off-3,base_y-38),(WIDTH//2+off-3,base_y+17),1)
            pygame.draw.ellipse(screen,(10,11,11),(WIDTH//2+off-6,base_y-43,12,7))
        pygame.draw.rect(screen,(38,39,36),(WIDTH//2-18,base_y+39,36,62),border_radius=3)
        pygame.draw.rect(screen,(95,66,43),(WIDTH//2-13,base_y+47,26,46),border_radius=2)
        pygame.draw.line(screen,(120,119,106),(WIDTH//2-39,base_y+29),(WIDTH//2+39,base_y+29),2)
        if t>0 and 0.35 < 1.35-t < 0.95:
            
            pygame.draw.line(screen,(19,20,19),(WIDTH//2-24,base_y-38),(WIDTH//2-42,base_y-4),5)
            pygame.draw.line(screen,(19,20,19),(WIDTH//2+24,base_y-38),(WIDTH//2+42,base_y-4),5)
            pygame.draw.circle(screen,(169,126,62),(WIDTH//2-17,base_y+1),6)
            pygame.draw.circle(screen,(169,126,62),(WIDTH//2+17,base_y+1),6)
            reach=int(18*math.sin((1.35-t-0.35)/0.60*math.pi))
            pygame.draw.line(screen,(83,76,62),(WIDTH//2-112,HEIGHT-8),(WIDTH//2-40,base_y+30+reach),17)
            pygame.draw.ellipse(screen,(95,78,59),(WIDTH//2-51,base_y+18+reach,25,18))
    else:
        
        pygame.draw.polygon(screen,(25,27,27),[(WIDTH//2-46,HEIGHT),(WIDTH//2-31,base_y+23),(WIDTH//2+31,base_y+23),(WIDTH//2+46,HEIGHT)])
        pygame.draw.polygon(screen,(44,47,46),[(WIDTH//2-31,base_y-5),(WIDTH//2+31,base_y-5),(WIDTH//2+27,base_y+48),(WIDTH//2-27,base_y+48)])
        pygame.draw.rect(screen,(83,87,82),(WIDTH//2-28,base_y-19,56,30),border_radius=3)
        pygame.draw.line(screen,(151,151,139),(WIDTH//2-24,base_y-16),(WIDTH//2+23,base_y-16),2)
        pygame.draw.rect(screen,(18,20,20),(WIDTH//2-7,base_y-23,14,5))
        pygame.draw.polygon(screen,(27,29,28),[(WIDTH//2-22,base_y+34),(WIDTH//2+22,base_y+34),(WIDTH//2+16,base_y+105),(WIDTH//2-15,base_y+105)])
        for yy in range(0,5):
            pygame.draw.line(screen,(72,74,68),(WIDTH//2-13,base_y+49+yy*10),(WIDTH//2+13,base_y+49+yy*10),1)
        pygame.draw.arc(screen,(120,120,109),(WIDTH//2-13,base_y+25,26,25),0,math.pi,2)
    if shot_flash>0:
        if weapon_type=="shotgun":
            pygame.draw.polygon(screen,(255,222,153),[(WIDTH//2,base_y-70),(WIDTH//2-38,base_y-4),(WIDTH//2-12,base_y-17),(WIDTH//2,base_y+8),(WIDTH//2+12,base_y-17),(WIDTH//2+38,base_y-4)])
        else:
            pygame.draw.polygon(screen,(255,210,135),[(WIDTH//2,base_y-44),(WIDTH//2-18,base_y+3),(WIDTH//2,base_y-8),(WIDTH//2+18,base_y+3)])

def draw_hud():
    pygame.draw.rect(screen,(12,8,15),(0,HEIGHT-49,WIDTH,49))
    pygame.draw.line(screen,(155,70,55),(0,HEIGHT-49),(WIDTH,HEIGHT-49),2)
    screen.blit(font.render(f"ЗДОРОВЬЕ {health}",True,(255,130,100)),(16,HEIGHT-39))
    weapon_label = f"ДВУСТВОЛКА {shotgun_loaded}|{ammo}" if weapon_type == "shotgun" else f"ПИСТОЛЕТ {ammo}"
    screen.blit(font.render(weapon_label,True,(255,210,130)),(250,HEIGHT-39))
    screen.blit(font.render(f"СЧЁТ {score}",True,(220,170,130)),(445,HEIGHT-39))
    remaining = sum(e["hp"]>0 for e in enemies)
    screen.blit(font.render(f"ВРАГИ {remaining}",True,(235,115,100)),(WIDTH-175,HEIGHT-39))
    if message_timer > 0:
        t = font.render(message,True,(255,225,190))
        screen.blit(t,t.get_rect(center=(WIDTH//2,30)))
    
    cx,cy=WIDTH//2,HALF_H
    pygame.draw.line(screen,(255,225,195),(cx-9,cy),(cx-3,cy),2)
    pygame.draw.line(screen,(255,225,195),(cx+3,cy),(cx+9,cy),2)
    pygame.draw.line(screen,(255,225,195),(cx,cy-9),(cx,cy-3),2)
    pygame.draw.line(screen,(255,225,195),(cx,cy+3),(cx,cy+9),2)
    

def draw_overlay(title, subtitle, hint):
    overlay=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
    overlay.fill((8,4,10,220))
    screen.blit(overlay,(0,0))
    a=big_font.render(title,True,(245,130,85))
    b=font.render(subtitle,True,(255,225,200))
    c=small_font.render(hint,True,(190,170,160))
    screen.blit(a,a.get_rect(center=(WIDTH//2,HEIGHT//2-55)))
    screen.blit(b,b.get_rect(center=(WIDTH//2,HEIGHT//2+5)))
    screen.blit(c,c.get_rect(center=(WIDTH//2,HEIGHT//2+55)))

def try_exit():
    global level_complete, game_won, message, message_timer
    if math.hypot(player_x-exit_pos[0],player_y-exit_pos[1]) < 1.15:
        if has_key:
            if level == 2:
                game_won = True
            else:
                level_complete = True
        else:
            message, message_timer = "Дверь заперта. Найди ключ-карту!", 1.5

setup_level(0)
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)
running=True

while running:
    dt=min(clock.tick(FPS)/1000,0.05)
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        elif event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                running=False
            elif not game_over and not game_won and not level_complete:
                if event.key==pygame.K_SPACE:
                    shoot()
                elif event.key==pygame.K_e:
                    try_exit()
                elif event.key==pygame.K_r:
                    start_reload()
                elif event.key==pygame.K_1:
                    weapon_type = "pistol"
                elif event.key==pygame.K_2 and shotgun_owned:
                    weapon_type = "shotgun"
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and not game_over and not game_won and not level_complete:
            shoot()
        elif event.type==pygame.MOUSEMOTION and not game_over and not game_won and not level_complete:
            player_angle += event.rel[0]*0.003

    if not game_over and not game_won and not level_complete:
        keys=pygame.key.get_pressed()
        move=2.55*dt
        turn=1.8*dt
        if keys[pygame.K_LEFT]: player_angle-=turn
        if keys[pygame.K_RIGHT]: player_angle+=turn
        forward=int(keys[pygame.K_w] or keys[pygame.K_UP])-int(keys[pygame.K_s] or keys[pygame.K_DOWN])
        strafe=int(keys[pygame.K_d])-int(keys[pygame.K_a])
        dx=(math.cos(player_angle)*forward+math.cos(player_angle+math.pi/2)*strafe)*move
        dy=(math.sin(player_angle)*forward+math.sin(player_angle+math.pi/2)*strafe)*move
        if dx and not is_wall(player_x+dx+math.copysign(0.16,dx),player_y): player_x+=dx
        if dy and not is_wall(player_x,player_y+dy+math.copysign(0.16,dy)): player_y+=dy

        
        if not has_key and math.hypot(player_x-key_pos[0],player_y-key_pos[1])<0.55:
            has_key=True
            message,message_timer="Ключ-карта найдена! Теперь ищи дверь.",2.5

        
        for item in pickups[:]:
            if math.hypot(player_x-item["x"], player_y-item["y"]) < 0.48:
                if item["kind"] == "shotgun":
                    shotgun_owned = True
                    weapon_type = "shotgun"
                    shotgun_loaded = min(2, ammo)
                    ammo -= shotgun_loaded
                    message, message_timer = "ДВУСТВОЛКА НАЙДЕНА! Нажми R для перезарядки.", 2.0
                    pickups.remove(item)
                elif item["kind"] == "health":
                    gained = min(item["amount"], 100-health)
                    if gained > 0:
                        health += gained
                        message, message_timer = f"+{gained} ЗДОРОВЬЯ", 1.0
                        pickups.remove(item)
                else:
                    gained = item["amount"]
                    ammo += gained
                    message, message_timer = f"+{gained} ПАТРОНОВ", 1.0
                    pickups.remove(item)

        for enemy in enemies:
            if enemy["hp"]<=0: continue
            enemy["cooldown"]-=dt
            dist=math.hypot(player_x-enemy["x"],player_y-enemy["y"])
            if dist<7 and enemy["cooldown"]<=0 and line_of_sight(enemy["x"],enemy["y"],player_x,player_y):
                health-=5+level
                enemy["cooldown"]=random.uniform(1.0, 2.0)
                enemy["attack_flash"]=0.12
               
            if 1.15<dist<7 and line_of_sight(enemy["x"],enemy["y"],player_x,player_y):
                step=enemy["speed"]*dt
                ex=(player_x-enemy["x"])/dist*step
                ey=(player_y-enemy["y"])/dist*step
                if not is_wall(enemy["x"]+ex,enemy["y"]): enemy["x"]+=ex
                if not is_wall(enemy["x"],enemy["y"]+ey): enemy["y"]+=ey
        shot_flash=max(0,shot_flash-dt)
        weapon_kick=max(0.0, weapon_kick-dt*5.5)
        weapon_anim=max(0.0,weapon_anim-dt)
        if reload_timer>0:
            reload_timer=max(0.0,reload_timer-dt)
            if reload_timer==0:
                loaded=min(2-shotgun_loaded,ammo)
                shotgun_loaded+=loaded
                ammo-=loaded
                message,message_timer="Двустволка перезаряжена",0.8
        for enemy in enemies:
            enemy["attack_flash"]=max(0.0,enemy.get("attack_flash",0.0)-dt)
        message_timer=max(0,message_timer-dt)
        if health<=0: game_over=True

    z=draw_world()
    if not game_over and not game_won and not level_complete:
        draw_key_and_exit(z)
        draw_supply_pickups(z)
        for e in sorted(enemies,key=lambda a:math.hypot(a["x"]-player_x,a["y"]-player_y),reverse=True):
            if e["hp"]>0: draw_demon(e,z)
        draw_weapon()
        draw_hud()
    elif level_complete:
        draw_overlay("ПРОХОД ОТКРЫТ",
                     "За дверью тебя ждёт следующий участок.",
                     "Нажми ENTER, чтобы продолжить, или ESC для выхода")
        if pygame.key.get_pressed()[pygame.K_RETURN]:
            if level == 1 and floor_index == 0:
                
                setup_level(1, 1)
            else:
                setup_level(level+1, 0)
            level_complete=False
    elif game_won:
        draw_overlay("СПАСИБО ЗА ПРОХОЖДЕНИЕ",
                     "Спасибо, что сыграл в ASHEN GATE!",
                     "Следующие версии скоро. Нажми ESC, чтобы выйти")
    else:
        draw_overlay("ПУТЬ ОБОРВАН",
                     f"Итоговый счёт: {score}",
                     "Нажми ESC, чтобы выйти")
    pygame.display.flip()

pygame.quit()
sys.exit()
