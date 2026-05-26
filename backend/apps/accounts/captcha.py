import base64
import hashlib
import random
import secrets
import struct
import zlib
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone


CAPTCHA_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CAPTCHA_LENGTH = 5
CAPTCHA_MAX_AGE_SECONDS = 5 * 60
CAPTCHA_SALT = "mentriq360-login-captcha"

CAPTCHA_FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
}


@dataclass(frozen=True)
class CaptchaChallenge:
    challenge_id: str
    image: str
    expires_in: int
    expires_at: str


def normalize_captcha_answer(value: str) -> str:
    return "".join(str(value or "").upper().split())


def _hash_answer(answer: str, nonce: str) -> str:
    material = f"{normalize_captcha_answer(answer)}:{nonce}:{settings.SECRET_KEY}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def make_captcha_token(answer: str, *, nonce: str | None = None) -> str:
    token_nonce = nonce or secrets.token_urlsafe(12)
    payload = {
        "nonce": token_nonce,
        "answer_hash": _hash_answer(answer, token_nonce),
    }
    return signing.dumps(payload, salt=CAPTCHA_SALT, compress=True)


def _blend_pixel(pixels: bytearray, width: int, height: int, x: int, y: int, color: tuple[int, int, int], alpha: float) -> None:
    if x < 0 or y < 0 or x >= width or y >= height:
        return
    index = (y * width + x) * 3
    for offset, channel in enumerate(color):
        pixels[index + offset] = int(pixels[index + offset] * (1 - alpha) + channel * alpha)


def _draw_rect(pixels: bytearray, width: int, height: int, x: int, y: int, size: int, color: tuple[int, int, int]) -> None:
    for yy in range(y, y + size):
        for xx in range(x, x + size):
            _blend_pixel(pixels, width, height, xx, yy, color, 0.95)


def _draw_line(
    pixels: bytearray,
    width: int,
    height: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: tuple[int, int, int],
    alpha: float,
) -> None:
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    step_x = 1 if x1 < x2 else -1
    step_y = 1 if y1 < y2 else -1
    error = dx + dy
    while True:
        _blend_pixel(pixels, width, height, x1, y1, color, alpha)
        _blend_pixel(pixels, width, height, x1 + 1, y1, color, alpha * 0.55)
        if x1 == x2 and y1 == y2:
            break
        doubled_error = 2 * error
        if doubled_error >= dy:
            error += dy
            x1 += step_x
        if doubled_error <= dx:
            error += dx
            y1 += step_y


def _png_bytes(width: int, height: int, pixels: bytearray) -> bytes:
    raw_rows = []
    row_length = width * 3
    for y in range(height):
        start = y * row_length
        raw_rows.append(b"\x00" + bytes(pixels[start : start + row_length]))
    raw = b"".join(raw_rows)

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        checksum = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _captcha_png(code: str) -> bytes:
    width = 184
    height = 58
    rng = random.SystemRandom()
    pixels = bytearray(width * height * 3)

    for y in range(height):
        for x in range(width):
            index = (y * width + x) * 3
            shade = 244 - int((x / width) * 18) - int((y / height) * 10)
            pixels[index : index + 3] = bytes((shade, min(255, shade + 4), min(255, shade + 10)))

    for _ in range(120):
        _blend_pixel(
            pixels,
            width,
            height,
            rng.randint(0, width - 1),
            rng.randint(0, height - 1),
            rng.choice([(15, 23, 42), (37, 99, 235), (185, 28, 28), (71, 85, 105)]),
            rng.uniform(0.15, 0.35),
        )

    for _ in range(9):
        _draw_line(
            pixels,
            width,
            height,
            rng.randint(0, width),
            rng.randint(0, height),
            rng.randint(0, width),
            rng.randint(0, height),
            rng.choice([(15, 23, 42), (37, 99, 235), (220, 38, 38), (4, 120, 87)]),
            rng.uniform(0.16, 0.32),
        )

    for index, character in enumerate(code):
        pattern = CAPTCHA_FONT[character]
        scale = rng.choice((4, 5))
        base_x = 16 + index * 31 + rng.randint(-2, 2)
        base_y = rng.randint(9, 15)
        slant = rng.choice((-1, 0, 1))
        color = rng.choice([(127, 29, 29), (30, 64, 175), (15, 23, 42), (4, 120, 87)])
        for row_index, row in enumerate(pattern):
            row_shift = (row_index - 3) * slant
            for col_index, enabled in enumerate(row):
                if enabled == "1":
                    _draw_rect(
                        pixels,
                        width,
                        height,
                        base_x + col_index * scale + row_shift,
                        base_y + row_index * scale,
                        scale,
                        color,
                    )

    for _ in range(3):
        y = rng.randint(18, 42)
        _draw_line(pixels, width, height, 4, y, width - 4, rng.randint(14, 44), (15, 23, 42), 0.18)

    return _png_bytes(width, height, pixels)


def generate_captcha_challenge() -> CaptchaChallenge:
    code = "".join(secrets.choice(CAPTCHA_ALPHABET) for _ in range(CAPTCHA_LENGTH))
    image = "data:image/png;base64," + base64.b64encode(_captcha_png(code)).decode("ascii")
    expires_at = timezone.now() + timedelta(seconds=CAPTCHA_MAX_AGE_SECONDS)
    return CaptchaChallenge(
        challenge_id=make_captcha_token(code),
        image=image,
        expires_in=CAPTCHA_MAX_AGE_SECONDS,
        expires_at=expires_at.isoformat(),
    )


def validate_captcha_response(challenge_id: str, answer: str) -> bool:
    if not challenge_id or not answer:
        return False
    try:
        payload = signing.loads(challenge_id, salt=CAPTCHA_SALT, max_age=CAPTCHA_MAX_AGE_SECONDS)
    except signing.BadSignature:
        return False
    nonce = payload.get("nonce")
    expected_hash = payload.get("answer_hash")
    if not nonce or not expected_hash:
        return False
    return secrets.compare_digest(_hash_answer(answer, nonce), expected_hash)
