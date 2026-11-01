from security.strength import meets_minimum, rate


def test_common_password_is_very_weak():
    assert rate("password")["rating"] == "Very Weak"
    assert rate("123456")["rating"] == "Very Weak"


def test_short_simple_password_is_weak_or_worse():
    assert rate("abc123")["rating"] in ("Very Weak", "Weak")


def test_long_random_password_is_very_strong():
    result = rate("xQ7#mZ2$vL9!pR4@wK6&")
    assert result["rating"] in ("Strong", "Very Strong")


def test_passphrase_style_password_is_strong():
    result = rate("correct-horse-battery-staple-42")
    assert result["rating"] in ("Fair", "Strong", "Very Strong")


def test_common_password_as_substring_is_still_flagged():
    # "MyPassword123!" contains the common password "password" — the check
    # must catch this, not just an exact full-string match.
    result = rate("MyPassword123!")
    assert "contains a common password" in result["issues"]
    assert result["rating"] == "Very Weak"


def test_empty_password_scores_zero():
    result = rate("")
    assert result["bits"] == 0
    assert result["rating"] == "Very Weak"


def test_meets_minimum_respects_ordering():
    assert meets_minimum("xQ7#mZ2$vL9!pR4@wK6&", "Fair") is True
    assert meets_minimum("password", "Fair") is False
