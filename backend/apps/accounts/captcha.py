import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone


CAPTCHA_ALPHABET = "0123456789"
CAPTCHA_LENGTH = 5
CAPTCHA_MAX_AGE_SECONDS = 5 * 60
CAPTCHA_SALT = "mentriq360-login-captcha"


@dataclass(frozen=True)
class CaptchaChallenge:
    challenge_id: str
    code: str
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


def generate_captcha_challenge() -> CaptchaChallenge:
    code = "".join(secrets.choice(CAPTCHA_ALPHABET) for _ in range(CAPTCHA_LENGTH))
    expires_at = timezone.now() + timedelta(seconds=CAPTCHA_MAX_AGE_SECONDS)
    return CaptchaChallenge(
        challenge_id=make_captcha_token(code),
        code=code,
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
