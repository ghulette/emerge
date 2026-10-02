"""Rendering emoji turtle shapes with the system's color emoji font."""

import math
import warnings

import pygame

FONT_NAMES = "applecoloremoji,segoeuiemoji,notocoloremoji"
FONT_PATHS = (
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "C:/Windows/Fonts/seguiemj.ttf",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
)
# Bitmap emoji fonts snap to their nearest built-in size, typically ~100-160px.
RENDER_SIZE = 128
# Rotations are rounded to this many degrees so cached images can be reused.
ANGLE_STEP = 3
MAX_CACHE = 5000

ORIENTS = (None, "rotate", "flip_x", "flip_y", "flip_xy")


def orientation(orient: str | None, heading: float, facing: float) -> tuple[bool, bool, int]:
    """How to transform an emoji drawn facing `facing` for a turtle heading
    `heading`. Returns (flip_x, flip_y, angle), where angle is a pygame
    rotation in degrees (counterclockwise), applied after flipping.
    """
    if orient not in ORIENTS:
        raise ValueError(f"shape_orient must be one of {ORIENTS}, not {orient!r}")
    if orient is None:
        return False, False, 0
    if orient == "rotate":
        angle = round((facing - heading) / ANGLE_STEP) * ANGLE_STEP % 360
        return False, False, angle
    h, f = math.radians(heading), math.radians(facing)
    # Flip when the heading points to the opposite side from the emoji's
    # facing: east vs. west for x, north vs. south for y.
    flip_x = orient in ("flip_x", "flip_xy") and math.sin(h) * math.sin(f) < -1e-9
    flip_y = orient in ("flip_y", "flip_xy") and math.cos(h) * math.cos(f) < -1e-9
    return flip_x, flip_y, 0


class EmojiRenderer:
    """Renders emoji at any size and orientation, caching the results."""

    def __init__(self):
        self._font: pygame.font.Font | None = None
        self._font_loaded = False
        self._base: dict[str, pygame.Surface | None] = {}
        self._cache: dict[tuple, pygame.Surface] = {}

    def _load_font(self) -> pygame.font.Font | None:
        if not self._font_loaded:
            self._font_loaded = True
            if not pygame.font.get_init():
                pygame.font.init()
            path =pygame.font.match_font(FONT_NAMES)
            candidates = ([path] if path else []) + list(FONT_PATHS)
            for candidate in candidates:
                try:
                    self._font = pygame.font.Font(candidate, RENDER_SIZE)
                    break
                except (OSError, FileNotFoundError, pygame.error):
                    continue
            else:
                warnings.warn("no color emoji font found; drawing emoji turtles as arrows")
        return self._font

    def _base_image(self, emoji: str) -> pygame.Surface | None:
        """The emoji at full render size, cropped to its visible pixels, or
        None if it can't be drawn.
        """
        if emoji not in self._base:
            image = None
            font = self._load_font()
            if font is not None:
                rendered = font.render(emoji, True, (255, 255, 255))
                bounds = rendered.get_bounding_rect()
                if bounds.width and bounds.height:
                    image = rendered.subsurface(bounds).copy()
                else:
                    warnings.warn(f"emoji font has no glyph for {emoji!r}; drawing an arrow")
            self._base[emoji] = image
        return self._base[emoji]

    def image(
        self, emoji: str, size: int, orient: str | None, heading: float, facing: float
    ) -> pygame.Surface | None:
        """The emoji scaled to fit a `size`-pixel square and oriented for
        `heading`, or None if it can't be drawn.
        """
        flip_x, flip_y, angle = orientation(orient, heading, facing)
        key = (emoji, size, flip_x, flip_y, angle)
        image = self._cache.get(key)
        if image is None:
            base = self._base_image(emoji)
            if base is None:
                return None
            w, h = base.get_size()
            fit = max(1, size) / max(w, h)
            image = pygame.transform.smoothscale(base, (max(1, round(w * fit)), max(1, round(h * fit))))
            if flip_x or flip_y:
                image = pygame.transform.flip(image, flip_x, flip_y)
            if angle:
                image = pygame.transform.rotozoom(image, angle, 1)
            if len(self._cache) >= MAX_CACHE:
                self._cache.clear()
            self._cache[key] = image
        return image
