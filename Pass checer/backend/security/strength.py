"""
Server-side password strength scoring.

This mirrors the client-side logic in frontend/script.js (same character-pool
entropy model, same pattern penalties) so registration enforces the same
standard the analyzer page shows the user — the server can never trust a
client-computed score, so it recomputes its own from the raw password. The
password itself is used only in memory here and is never logged or persisted.
"""

import math
import re

COMMON_PASSWORDS = {
    "password", "123456", "12345678", "123456789", "qwerty", "abc123", "111111",
    "123123", "admin", "letmein", "welcome", "monkey", "dragon", "iloveyou",
    "password1", "qwerty123", "1q2w3e4r", "sunshine", "princess", "football",
    "000000", "1234567", "12345", "qazwsx", "trustno1",
    "master", "passw0rd", "login", "starwars", "superman", "batman",
}

SEQUENCES = ["abcdefghijklmnopqrstuvwxyz", "01234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"]

# (max_bits_exclusive, rating, description)
SCALE = [
    (28, "Very Weak", "Cracked almost instantly"),
    (40, "Weak", "Vulnerable to fast attacks"),
    (60, "Fair", "Okay, but improvable"),
    (80, "Strong", "Solid protection"),
    (math.inf, "Very Strong", "Excellent — attacker's nightmare"),
]

RATING_ORDER = [label for _, label, _ in SCALE]


def _char_pool(password: str) -> int:
    pool = 0
    if re.search(r"[a-z]", password):
        pool += 26
    if re.search(r"[A-Z]", password):
        pool += 26
    if re.search(r"[0-9]", password):
        pool += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        pool += 33
    return pool


def detect_patterns(password: str) -> dict:
    issues = []
    critical = False
    lower = password.lower()

    if password:
        if lower in COMMON_PASSWORDS:
            issues.append("common password")
            critical = True
        else:
            for common in COMMON_PASSWORDS:
                if len(common) >= 5 and common in lower:
                    issues.append("contains a common password")
                    critical = True
                    break

    if re.search(r"(.)\1{2,}", password):
        issues.append("repeated characters")

    for seq in SEQUENCES:
        found = False
        for i in range(len(seq) - 2):
            chunk = seq[i:i + 3]
            if chunk in lower or chunk[::-1] in lower:
                issues.append("keyboard/alphabet sequence")
                found = True
                break
        if found:
            break

    if password and password.isdigit():
        issues.append("digits only")
    if password and password.isalpha():
        issues.append("letters only")
    if re.search(r"(19|20)\d{2}", password):
        issues.append("looks like a year")

    return {"issues": list(dict.fromkeys(issues)), "critical": critical}


def entropy_bits(password: str) -> int:
    if not password:
        return 0
    pool = _char_pool(password)
    if pool == 0:
        return 0
    bits = len(password) * math.log2(pool)
    result = detect_patterns(password)
    bits = max(0, bits - len(result["issues"]) * 12)
    if result["critical"]:
        bits = min(bits, 24)
    return round(bits)


def rate(password: str) -> dict:
    """Full analysis, safe to return to the client — no logging happens here
    and the caller must not log the password either."""
    bits = entropy_bits(password)
    for max_bits, label, description in SCALE:
        if bits < max_bits:
            rating, sub = label, description
            break
    issues = detect_patterns(password)["issues"] if password else []
    return {"bits": bits, "rating": rating, "description": sub, "issues": issues}


def meets_minimum(password: str, minimum_rating: str) -> bool:
    result = rate(password)
    return RATING_ORDER.index(result["rating"]) >= RATING_ORDER.index(minimum_rating)
