"""California residential lease rules (jurisdiction "us-ca").

Same contract as the PRC rules in checklist.py: every check returns
violation / ok / unknown, and a missing or unparseable clause is always
unknown, never a silent pass.
"""

from __future__ import annotations

import re

from contractguard.models import StatuteCheck, StatuteStatus


def _excerpt(text: str, needle: str, span: int = 60) -> str:
    """Clip a readable excerpt around a matched phrase."""
    idx = text.find(needle)
    if idx < 0:
        return needle
    start = max(0, idx - 10)
    end = min(len(text), idx + len(needle) + span)
    return text[start:end].strip()


_USD_RE = r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)"
_EN_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", text)


def _first_sentence(sentences: list[str], *needles: str, skip: str | None = None) -> str | None:
    """First sentence containing every needle (case-insensitive)."""
    for s in sentences:
        sl = s.lower()
        if skip and skip in sl:
            continue
        if all(n in sl for n in needles):
            return s
    return None


def _usd(sentence: str) -> tuple[float, str] | tuple[None, None]:
    """First dollar amount in a sentence, as (value, raw match)."""
    m = re.search(_USD_RE, sentence)
    if not m:
        return None, None
    return float(m.group(1).replace(",", "")), m.group(0)


def check_ca_security_deposit_cap(text: str, lang: str) -> StatuteCheck:
    """Residential security deposits are capped at one month's rent."""
    rule_id = "us_ca_security_deposit_cap"
    title = "Security deposit cap"
    basis = "California Civil Code §1950.5, as amended by AB 12 (effective 2024-07-01)"
    sentences = _sentences(text)
    deposit_s = _first_sentence(sentences, "security deposit") or _first_sentence(sentences, "deposit")
    rent_s = _first_sentence(sentences, "monthly rent") or _first_sentence(sentences, "rent", "$", skip="deposit")
    deposit, deposit_raw = _usd(deposit_s) if deposit_s else (None, None)
    rent, rent_raw = _usd(rent_s) if rent_s else (None, None)
    if deposit is not None and rent is not None:
        quote = _excerpt(text, deposit_raw)
        if deposit > rent:
            return StatuteCheck(
                rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.VIOLATION,
                detail=f"Security deposit of {deposit_raw} exceeds one month's rent ({rent_raw}); "
                "California caps residential security deposits at one month's rent.",
                quote=quote,
            )
        return StatuteCheck(
            rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.OK,
            detail=f"Security deposit of {deposit_raw} is within the one-month rent cap ({rent_raw} rent).",
            quote=quote,
        )
    # deposits are often written as "two months' rent" with no dollar figure
    m = re.search(
        r"security deposit[^.]{0,50}?\b(one|two|three|four|five|six|[0-9]+)\s+months'? rent",
        text, re.IGNORECASE,
    )
    if m:
        months = int(m.group(1)) if m.group(1).isdigit() else _EN_NUM[m.group(1).lower()]
        quote = _excerpt(text, m.group(0))
        if months > 1:
            return StatuteCheck(
                rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.VIOLATION,
                detail=f"Security deposit is set at {months} months' rent; the statutory cap is one month.",
                quote=quote,
            )
        return StatuteCheck(
            rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.OK,
            detail="Security deposit is set at one month's rent, within the statutory cap.",
            quote=quote,
        )
    return StatuteCheck(
        rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.UNKNOWN,
        detail="No explicit security deposit amount or monthly rent found, "
        "so the one-month cap cannot be checked.",
        quote=_excerpt(text, deposit_s.strip()[:40]) if deposit_s else "",
    )


_NONREFUNDABLE_MARKERS = (
    "non-refundable", "nonrefundable", "shall be retained",
    "will not be returned", "not be refunded", "shall not be returned",
)


def check_ca_deposit_refundability(text: str, lang: str) -> StatuteCheck:
    """Every residential security deposit must be refundable."""
    rule_id = "us_ca_deposit_refundability"
    title = "Security deposit refundability"
    basis = "California Civil Code §1950.5"
    deposit_sentences = [s for s in _sentences(text) if "deposit" in s.lower()]
    for s in deposit_sentences:
        sl = s.lower()
        for marker in _NONREFUNDABLE_MARKERS:
            idx = sl.find(marker)
            if idx >= 0:
                return StatuteCheck(
                    rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.VIOLATION,
                    detail="The security deposit is declared non-refundable; California makes "
                    "every residential security deposit refundable.",
                    quote=_excerpt(text, s[idx:idx + len(marker)]),
                )
    if deposit_sentences:
        return StatuteCheck(
            rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.OK,
            detail="A security deposit is collected with no non-refundable language; "
            "residential deposits must be refundable by statute.",
            quote=_excerpt(text, deposit_sentences[0].strip()[:40]),
        )
    return StatuteCheck(
        rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.UNKNOWN,
        detail="No security deposit clause found.",
    )


_ENTRY_NO_NOTICE = (
    "with or without notice", "without prior notice", "without advance notice",
    "without written notice", "without notice",
)


def check_ca_entry_notice(text: str, lang: str) -> StatuteCheck:
    """Landlord entry needs reasonable advance notice, presumed to be 24 hours in writing."""
    rule_id = "us_ca_entry_notice"
    title = "Landlord entry notice"
    basis = "California Civil Code §1954"
    entry_sentences = [
        s for s in _sentences(text) if re.search(r"enter|entry|access", s, re.IGNORECASE)
    ]
    for s in entry_sentences:
        sl = s.lower()
        for marker in _ENTRY_NO_NOTICE:
            idx = sl.find(marker)
            if idx >= 0:
                return StatuteCheck(
                    rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.VIOLATION,
                    detail=f"The landlord may enter {marker}; California requires reasonable "
                    "advance notice, presumed to be 24 hours in writing.",
                    quote=_excerpt(text, s[idx:idx + len(marker)]),
                )
        # "enter at any time" is the same waiver in plainer words, but only when the
        # landlord is the one entering and no emergency exception is being stated
        if "at any time" in sl and "landlord" in sl and "emergenc" not in sl:
            return StatuteCheck(
                rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.VIOLATION,
                detail="The landlord may enter at any time; California requires reasonable "
                "advance notice, presumed to be 24 hours in writing.",
                quote=_excerpt(text, "at any time"),
            )
    for s in entry_sentences:
        m = re.search(
            r"([0-9]+)\s*\)?\s*hours?[^.]{0,30}?notice|notice[^.]{0,30}?([0-9]+)\s*\)?\s*hours?",
            s, re.IGNORECASE,
        )
        if not m:
            continue
        hours = int(m.group(1) or m.group(2))
        if hours < 24:
            return StatuteCheck(
                rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.VIOLATION,
                detail=f"Entry notice of {hours} hours is below the 24-hour floor California "
                "presumes reasonable.",
                quote=_excerpt(text, m.group(0)),
            )
        return StatuteCheck(
            rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.OK,
            detail=f"Landlord entry requires {hours} hours' notice, meeting the 24-hour "
            "statutory floor.",
            quote=_excerpt(text, m.group(0)),
        )
    if any(re.search(r"reasonable (?:advance )?notice", s, re.IGNORECASE) for s in entry_sentences):
        return StatuteCheck(
            rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.UNKNOWN,
            detail="Entry requires 'reasonable' notice with no hours stated; 24 hours is the "
            "presumed floor, which the text does not confirm.",
        )
    return StatuteCheck(
        rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.UNKNOWN,
        detail="No landlord entry clause found.",
    )


def check_ca_deposit_return(text: str, lang: str) -> StatuteCheck:
    """The deposit (less itemized deductions) must come back within 21 days of move-out."""
    rule_id = "us_ca_deposit_return_deadline"
    title = "Deposit return deadline"
    basis = "California Civil Code §1950.5(g)"
    deposit_sentences = [s for s in _sentences(text) if "deposit" in s.lower()]
    for s in deposit_sentences:
        if not re.search(r"return|refund|itemiz", s, re.IGNORECASE):
            continue
        m = re.search(r"([0-9]+)\s*\)?\s*days", s)
        if not m:
            continue  # "promptly returned" and friends carry no checkable number
        days = int(m.group(1))
        quote = _excerpt(text, m.group(0))
        if days > 21:
            return StatuteCheck(
                rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.VIOLATION,
                detail=f"Deposit return is set at {days} days after move-out; the statutory "
                "deadline is 21 days with an itemized statement.",
                quote=quote,
            )
        return StatuteCheck(
            rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.OK,
            detail=f"Deposit is returned within {days} days, inside the 21-day statutory deadline.",
            quote=quote,
        )
    if deposit_sentences:
        return StatuteCheck(
            rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.UNKNOWN,
            detail="A deposit is collected but no return deadline is stated; the statute gives "
            "21 days with an itemized statement, which the text does not confirm.",
            quote=_excerpt(text, deposit_sentences[0].strip()[:40]),
        )
    return StatuteCheck(
        rule_id=rule_id, title=title, basis=basis, status=StatuteStatus.UNKNOWN,
        detail="No security deposit clause found.",
    )


RULES = [
    check_ca_security_deposit_cap,
    check_ca_deposit_refundability,
    check_ca_entry_notice,
    check_ca_deposit_return,
]
