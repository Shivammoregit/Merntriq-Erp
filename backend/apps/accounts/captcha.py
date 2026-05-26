import base64
import hashlib
import html
import random
import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone


CAPTCHA_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CAPTCHA_LENGTH = 5
CAPTCHA_MAX_AGE_SECONDS = 5 * 60
CAPTCHA_SALT = "mentriq360-login-captcha"


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


def _captcha_svg(code: str) -> str:
    width = 184
    height = 58
    random_seed = random.SystemRandom()
    lines = []
    for _ in range(7):
        x1 = random_seed.randint(0, width)
        y1 = random_seed.randint(0, height)
        x2 = random_seed.randint(0, width)
        y2 = random_seed.randint(0, height)
        color = random_seed.choice(["#94a3b8", "#64748b", "#2563eb", "#ef4444", "#0f172a"])
        opacity = random_seed.choice(["0.18", "0.22", "0.28"])
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.2" opacity="{opacity}" />')

    dots = []
    for _ in range(42):
        cx = random_seed.randint(3, width - 3)
        cy = random_seed.randint(3, height - 3)
        dots.append(f'<circle cx="{cx}" cy="{cy}" r="1" fill="#64748b" opacity="0.28" />')

    letters = []
    x = 24
    for index, character in enumerate(code):
        rotation = random_seed.randint(-18, 18)
        y = random_seed.randint(34, 43)
        fill = random_seed.choice(["#b91c1c", "#1d4ed8", "#0f172a", "#047857"])
        safe_character = html.escape(character)
        letters.append(
            f'<text x="{x + index * 29}" y="{y}" rotate="{rotation}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="31" '
            f'font-weight="800" fill="{fill}">{safe_character}</text>'
        )

    wave_path = "M4 30 C34 12, 58 46, 90 28 S142 12, 180 35"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
        "<defs>"
        '<linearGradient id="captchaBg" x1="0" x2="1" y1="0" y2="1">'
        '<stop offset="0" stop-color="#f8fafc" />'
        '<stop offset="1" stop-color="#e2e8f0" />'
        "</linearGradient>"
        "</defs>"
        '<rect width="184" height="58" rx="8" fill="url(#captchaBg)" />'
        f"{''.join(dots)}"
        f"{''.join(lines)}"
        f'<path d="{wave_path}" fill="none" stroke="#0f172a" stroke-width="1.5" opacity="0.2" />'
        f"{''.join(letters)}"
        "</svg>"
    )


def generate_captcha_challenge() -> CaptchaChallenge:
    code = "".join(secrets.choice(CAPTCHA_ALPHABET) for _ in range(CAPTCHA_LENGTH))
    svg = _captcha_svg(code)
    image = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
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
