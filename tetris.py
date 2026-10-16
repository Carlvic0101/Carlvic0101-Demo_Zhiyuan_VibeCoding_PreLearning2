"""
俄罗斯方块 (Tetris)
操作说明:
  ← → : 左右移动
  ↓   : 软降
  ↑ / X : 顺时针旋转
  Z     : 逆时针旋转
  空格  : 硬降（瞬间落地）
  C     : 暂存方块 (Hold)
  P     : 暂停
  R     : 重新开始（游戏结束后）
"""

from __future__ import annotations

import random
import sys
from typing import List, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
CELL = 30
COLS, ROWS = 10, 20
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
SIDE_W = 200
WIN_W, WIN_H = BOARD_W + SIDE_W, BOARD_H

FPS = 60
LOCK_DELAY_MS = 500
DAS_MS = 170
ARR_MS = 40

# 颜色
BG = (18, 18, 28)
GRID = (40, 40, 55)
BORDER = (90, 90, 120)
TEXT = (230, 230, 240)
MUTED = (140, 140, 160)
GHOST_A = 70

# 七种方块颜色
COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

# 每种方块 4 个旋转态（相对坐标）
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

# SRS 踢墙偏移（JLSTZ / I）
KICKS_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
}

KICKS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
}

LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
class Piece:
    def __init__(self, kind: str):
        self.kind = kind
        self.rot = 0
        self.x = 3
        self.y = -1 if kind != "I" else -2

    def cells(self, rot: Optional[int] = None, ox: int = 0, oy: int = 0) -> List[Tuple[int, int]]:
        r = self.rot if rot is None else rot
        return [(self.x + cx + ox, self.y + cy + oy) for cx, cy in SHAPES[self.kind][r]]


class Bag:
    """7-bag 随机生成器"""

    def __init__(self):
        self._bag: List[str] = []
        self._refill()

    def _refill(self) -> None:
        kinds = list(SHAPES.keys())
        random.shuffle(kinds)
        self._bag.extend(kinds)

    def next(self) -> Piece:
        if not self._bag:
            self._refill()
        return Piece(self._bag.pop(0))

    def peek(self, n: int = 5) -> List[str]:
        while len(self._bag) < n:
            self._refill()
        return self._bag[:n]


# ---------------------------------------------------------------------------
# 游戏逻辑
# ---------------------------------------------------------------------------
class Tetris:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.board: List[List[Optional[str]]] = [[None] * COLS for _ in range(ROWS)]
        self.bag = Bag()
        self.current = self.bag.next()
        self.hold: Optional[str] = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.lock_timer: Optional[int] = None
        self.fall_acc = 0.0
        if not self._valid(self.current):
            self.game_over = True

    def fall_interval(self) -> float:
        # 关卡越高下落越快（秒）
        return max(0.05, 0.8 * (0.85 ** (self.level - 1)))

    def _valid(self, piece: Piece, rot: Optional[int] = None, ox: int = 0, oy: int = 0) -> bool:
        for x, y in piece.cells(rot, ox, oy):
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def move(self, dx: int, dy: int) -> bool:
        if self._valid(self.current, ox=dx, oy=dy):
            self.current.x += dx
            self.current.y += dy
            if dy:
                self.lock_timer = None
            elif not self._valid(self.current, oy=1):
                self.lock_timer = pygame.time.get_ticks()
            return True
        return False

    def rotate(self, clockwise: bool = True) -> bool:
        piece = self.current
        if piece.kind == "O":
            return True
        new_rot = (piece.rot + (1 if clockwise else -1)) % 4
        kicks = KICKS_I if piece.kind == "I" else KICKS_JLSTZ
        for kx, ky in kicks.get((piece.rot, new_rot), [(0, 0)]):
            if self._valid(piece, rot=new_rot, ox=kx, oy=-ky):
                piece.rot = new_rot
                piece.x += kx
                piece.y -= ky
                if not self._valid(piece, oy=1):
                    self.lock_timer = pygame.time.get_ticks()
                else:
                    self.lock_timer = None
                return True
        return False

    def hard_drop(self) -> None:
        dist = 0
        while self.move(0, 1):
            dist += 1
        self.score += dist * 2
        self._lock()

    def soft_drop_step(self) -> bool:
        if self.move(0, 1):
            self.score += 1
            return True
        return False

    def hold_piece(self) -> None:
        if not self.can_hold:
            return
        kind = self.current.kind
        if self.hold is None:
            self.hold = kind
            self.current = self.bag.next()
        else:
            self.hold, swapped = kind, self.hold
            self.current = Piece(swapped)
        self.can_hold = False
        self.lock_timer = None
        if not self._valid(self.current):
            self.game_over = True

    def ghost_y(self) -> int:
        gy = 0
        while self._valid(self.current, oy=gy + 1):
            gy += 1
        return self.current.y + gy

    def _lock(self) -> None:
        for x, y in self.current.cells():
            if y < 0:
                self.game_over = True
                return
            self.board[y][x] = self.current.kind
        cleared = self._clear_lines()
        if cleared:
            self.lines += cleared
            self.score += LINE_SCORES.get(cleared, 0) * self.level
            self.level = self.lines // 10 + 1
        self.current = self.bag.next()
        self.can_hold = True
        self.lock_timer = None
        self.fall_acc = 0.0
        if not self._valid(self.current):
            self.game_over = True

    def _clear_lines(self) -> int:
        new_board = [row for row in self.board if any(c is None for c in row)]
        cleared = ROWS - len(new_board)
        while len(new_board) < ROWS:
            new_board.insert(0, [None] * COLS)
        self.board = new_board
        return cleared

    def update(self, dt: float, soft: bool) -> None:
        if self.game_over or self.paused:
            return
        interval = 0.05 if soft else self.fall_interval()
        self.fall_acc += dt
        while self.fall_acc >= interval:
            self.fall_acc -= interval
            if not self.move(0, 1):
                now = pygame.time.get_ticks()
                if self.lock_timer is None:
                    self.lock_timer = now
                elif now - self.lock_timer >= LOCK_DELAY_MS:
                    self._lock()
                    break


# ---------------------------------------------------------------------------
# 绘制
# ---------------------------------------------------------------------------
def draw_cell(surf: pygame.Surface, x: int, y: int, color: Tuple[int, int, int], alpha: int = 255) -> None:
    if y < 0:
        return
    rect = pygame.Rect(x * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2)
    if alpha < 255:
        tmp = pygame.Surface((CELL - 2, CELL - 2), pygame.SRCALPHA)
        tmp.fill((*color, alpha))
        surf.blit(tmp, rect.topleft)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=3)
        highlight = tuple(min(255, c + 40) for c in color)
        pygame.draw.line(surf, highlight, rect.topleft, (rect.right - 1, rect.top), 2)
        pygame.draw.line(surf, highlight, rect.topleft, (rect.left, rect.bottom - 1), 2)


def draw_mini(surf: pygame.Surface, kind: str, ox: int, oy: int, scale: int = 18) -> None:
    shape = SHAPES[kind][0]
    color = COLORS[kind]
    xs = [c[0] for c in shape]
    ys = [c[1] for c in shape]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = (max_x - min_x + 1) * scale
    h = (max_y - min_y + 1) * scale
    base_x = ox - w // 2
    base_y = oy - h // 2
    for cx, cy in shape:
        rx = base_x + (cx - min_x) * scale
        ry = base_y + (cy - min_y) * scale
        pygame.draw.rect(surf, color, (rx + 1, ry + 1, scale - 2, scale - 2), border_radius=2)


def draw_game(screen: pygame.Surface, game: Tetris, font: pygame.font.Font, small: pygame.font.Font) -> None:
    screen.fill(BG)
    board_surf = pygame.Surface((BOARD_W, BOARD_H))
    board_surf.fill(BG)

    # 网格
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(board_surf, GRID, (c * CELL, r * CELL, CELL, CELL), 1)

    # 已锁定方块
    for y in range(ROWS):
        for x in range(COLS):
            kind = game.board[y][x]
            if kind:
                draw_cell(board_surf, x, y, COLORS[kind])

    if not game.game_over:
        # 幽灵
        gy = game.ghost_y()
        for x, y in game.current.cells(oy=gy - game.current.y):
            draw_cell(board_surf, x, y, COLORS[game.current.kind], GHOST_A)
        # 当前方块
        for x, y in game.current.cells():
            draw_cell(board_surf, x, y, COLORS[game.current.kind])

    pygame.draw.rect(board_surf, BORDER, board_surf.get_rect(), 2)
    screen.blit(board_surf, (0, 0))

    # 侧边栏
    sx = BOARD_W + 16
    screen.blit(font.render("SCORE", True, MUTED), (sx, 20))
    screen.blit(font.render(str(game.score), True, TEXT), (sx, 48))

    screen.blit(font.render("LEVEL", True, MUTED), (sx, 100))
    screen.blit(font.render(str(game.level), True, TEXT), (sx, 128))

    screen.blit(font.render("LINES", True, MUTED), (sx, 180))
    screen.blit(font.render(str(game.lines), True, TEXT), (sx, 208))

    screen.blit(font.render("HOLD", True, MUTED), (sx, 270))
    if game.hold:
        draw_mini(screen, game.hold, sx + 70, 320)

    screen.blit(font.render("NEXT", True, MUTED), (sx, 380))
    for i, kind in enumerate(game.bag.peek(5)):
        draw_mini(screen, kind, sx + 70, 430 + i * 55, scale=16)

    if game.paused and not game.game_over:
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))
        msg = font.render("暂停 (P)", True, TEXT)
        screen.blit(msg, (BOARD_W // 2 - msg.get_width() // 2, BOARD_H // 2 - 12))

    if game.game_over:
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        t1 = font.render("游戏结束", True, TEXT)
        t2 = small.render("按 R 重新开始", True, MUTED)
        screen.blit(t1, (BOARD_W // 2 - t1.get_width() // 2, BOARD_H // 2 - 30))
        screen.blit(t2, (BOARD_W // 2 - t2.get_width() // 2, BOARD_H // 2 + 10))


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------
def main() -> None:
    pygame.init()
    pygame.display.set_caption("俄罗斯方块")
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("microsoftyahei,simhei,arial", 22, bold=True)
    small = pygame.font.SysFont("microsoftyahei,simhei,arial", 16)

    game = Tetris()

    # 按键连发状态
    left_held = right_held = False
    left_das = right_das = 0
    left_arr = right_arr = 0

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0
        soft = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                elif event.key == pygame.K_r and game.game_over:
                    game.reset()
                elif game.game_over or game.paused:
                    continue
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    game.move(-1, 0)
                    left_held = True
                    left_das = pygame.time.get_ticks()
                    left_arr = 0
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    game.move(1, 0)
                    right_held = True
                    right_das = pygame.time.get_ticks()
                    right_arr = 0
                elif event.key in (pygame.K_UP, pygame.K_x, pygame.K_w):
                    game.rotate(True)
                elif event.key == pygame.K_z:
                    game.rotate(False)
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()
                elif event.key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
                    game.hold_piece()
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    left_held = False
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    right_held = False

        keys = pygame.key.get_pressed()
        if not game.game_over and not game.paused:
            soft = keys[pygame.K_DOWN] or keys[pygame.K_s]
            now = pygame.time.get_ticks()

            # DAS / ARR
            if left_held and not right_held:
                if now - left_das >= DAS_MS:
                    if left_arr == 0 or now - left_arr >= ARR_MS:
                        game.move(-1, 0)
                        left_arr = now
            if right_held and not left_held:
                if now - right_das >= DAS_MS:
                    if right_arr == 0 or now - right_arr >= ARR_MS:
                        game.move(1, 0)
                        right_arr = now

            game.update(dt, soft)

        draw_game(screen, game, font, small)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
