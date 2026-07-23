"""Deterministic statute checklist for Chinese contracts.

The LLM analysis is good at judgment calls, but a few rules in Chinese
labor and civil law are hard lines with numeric caps: probation length,
probation pay, penalty scope, non-compete duration and compensation,
earnest-money ratio, lease term. Those are checkable without a model,
and a wrong answer there is not an opinion, it is a violation.

Each rule returns one of three statuses:

- ``violation``: the contract breaks the rule, with the clause quoted.
- ``ok``: the relevant clause exists and stays within the cap.
- ``unknown``: the contract does not say enough to judge. We never claim
  "ok" when the clause is missing or unparseable; silence is not
  compliance.
"""

from __future__ import annotations

import re

from contractguard.models import StatuteCheck, StatuteStatus

_CN_NUM = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12,
}


def _cn_int(token: str) -> int | None:
    """Parse an integer written as digits or simple Chinese numerals."""
    token = token.strip()
    if token.isdigit():
        return int(token)
    if token in _CN_NUM:
        return _CN_NUM[token]
    if "十" in token:
        left, _, right = token.partition("十")
        tens = _CN_NUM.get(left, 1 if left == "" else -1)
        ones = _CN_NUM.get(right, 0 if right == "" else -1)
        if tens > 0 and ones >= 0:
            return tens * 10 + ones
    return None


def _search_number(
    patterns: list[str], text: str, skip_if_contains: str | None = None
) -> tuple[int, str] | tuple[None, None]:
    """Return (value, matched_excerpt) for the first usable match."""
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            if skip_if_contains and skip_if_contains in m.group(0):
                continue
            value = _cn_int(m.group(1))
            if value is not None:
                return value, m.group(0)
    return None, None


def _excerpt(text: str, needle: str, span: int = 60) -> str:
    """Clip a readable excerpt around a matched phrase."""
    idx = text.find(needle)
    if idx < 0:
        return needle
    start = max(0, idx - 10)
    end = min(len(text), idx + len(needle) + span)
    return text[start:end].strip()


_PROBATION_MONTHS = [
    r"试用期[^。；;]{0,12}?([0-9]+|[一二两三四五六七八九十]+)\s*个?月",
    r"[Pp]robation[^.]{0,40}?([0-9]+)\s*months?",
]
_CONTRACT_YEARS = [
    r"(?:合同|劳动合?同|本合同|租赁(?:合同|期限)?)[^。；;]{0,16}?([0-9]+|[一二两三四五六七八九十]+)\s*年",
    r"(?:fixed[- ]term|term|lease)[^.]{0,40}?([0-9]+)\s*years?",
]
_CONTRACT_MONTHS_ONLY = [
    r"(?:合同|本合同|期限)[^。；;]{0,16}?([0-9]+|[一二两三四五六七八九十]+)\s*个?月",
    r"(?:fixed[- ]term|term)[^.]{0,40}?([0-9]+)\s*months?",
]
_OPEN_ENDED = ["无固定期限", "open-ended", "open ended"]


def _probation_cap_months(term_months: int | None) -> int | None:
    """Statutory probation cap by contract term (LCL art. 19)."""
    if term_months is None:
        return None
    if term_months < 3:
        return 0
    if term_months < 12:
        return 1
    if term_months < 36:
        return 2
    return 6


def check_probation_duration(text: str, lang: str) -> StatuteCheck:
    """Probation period must not exceed the statutory cap for the term."""
    basis = "《劳动合同法》第十九条 / PRC Labor Contract Law, Art. 19"
    probation, probation_quote = _search_number(_PROBATION_MONTHS, text)
    if probation is None:
        return StatuteCheck(
            rule_id="cn_probation_duration_cap",
            title="试用期上限 / Probation cap",
            basis=basis,
            status=StatuteStatus.UNKNOWN,
            detail="未找到明确的试用期月数，无法判断 / No explicit probation length found.",
        )
    open_ended = any(marker in text for marker in _OPEN_ENDED)
    years, _ = _search_number(_CONTRACT_YEARS, text, skip_if_contains="试用")
    months, _ = _search_number(_CONTRACT_MONTHS_ONLY, text, skip_if_contains="试用")
    term_months = 120 if open_ended else (years * 12 if years is not None else months)
    cap = _probation_cap_months(term_months)
    if cap is None:
        return StatuteCheck(
            rule_id="cn_probation_duration_cap",
            title="试用期上限 / Probation cap",
            basis=basis,
            status=StatuteStatus.UNKNOWN,
            detail=f"试用期 {probation} 个月，但合同期限无法解析，无法核对上限 / "
            f"Probation is {probation} months, but the contract term is unparseable.",
            quote=probation_quote,
        )
    excerpt = _excerpt(text, probation_quote)
    if cap == 0:
        return StatuteCheck(
            rule_id="cn_probation_duration_cap",
            title="试用期上限 / Probation cap",
            basis=basis,
            status=StatuteStatus.VIOLATION,
            detail=f"合同期限不足 3 个月，依法不得约定试用期，却写了 {probation} 个月 / "
            f"Term under 3 months may not carry any probation, but {probation} months is stated.",
            quote=excerpt,
        )
    if probation > cap:
        return StatuteCheck(
            rule_id="cn_probation_duration_cap",
            title="试用期上限 / Probation cap",
            basis=basis,
            status=StatuteStatus.VIOLATION,
            detail=f"试用期 {probation} 个月超出法定上限 {cap} 个月 / "
            f"Probation of {probation} months exceeds the statutory cap of {cap}.",
            quote=excerpt,
        )
    return StatuteCheck(
        rule_id="cn_probation_duration_cap",
        title="试用期上限 / Probation cap",
        basis=basis,
        status=StatuteStatus.OK,
        detail=f"试用期 {probation} 个月在上限 {cap} 个月之内 / "
        f"Probation of {probation} months is within the {cap}-month cap.",
        quote=excerpt,
    )


def check_probation_wage(text: str, lang: str) -> StatuteCheck:
    """Probation pay must be at least 80% of the agreed wage (LCL art. 20)."""
    basis = "《劳动合同法》第二十条 / PRC Labor Contract Law, Art. 20"
    m = re.search(r"试用期工资[^。；;]{0,20}?([0-9]+)\s*%", text)
    if not m:
        m = re.search(r"[Pp]robation[^.]{0,40}?([0-9]+)\s*%[^.]{0,20}(?:wage|salary|pay)", text)
    if not m:
        m = re.search(r"试用期工资[^。；;]{0,10}?(八|九)折", text)
        if m:
            ratio = 80 if m.group(1) == "八" else 90
            return _wage_verdict(ratio, basis, m.group(0), text)
        return StatuteCheck(
            rule_id="cn_probation_wage_floor",
            title="试用期工资底线 / Probation wage floor",
            basis=basis,
            status=StatuteStatus.UNKNOWN,
            detail="未找到试用期工资的比例或金额，无法判断 / No probation wage ratio or figure found.",
        )
    return _wage_verdict(int(m.group(1)), basis, m.group(0), text)


def _wage_verdict(ratio: int, basis: str, needle: str, text: str) -> StatuteCheck:
    if ratio < 80:
        return StatuteCheck(
            rule_id="cn_probation_wage_floor",
            title="试用期工资底线 / Probation wage floor",
            basis=basis,
            status=StatuteStatus.VIOLATION,
            detail=f"试用期工资仅为约定工资的 {ratio}%，低于法定 80% 底线 / "
            f"Probation pay is {ratio}% of the agreed wage, below the 80% floor.",
            quote=_excerpt(text, needle),
        )
    return StatuteCheck(
        rule_id="cn_probation_wage_floor",
        title="试用期工资底线 / Probation wage floor",
        basis=basis,
        status=StatuteStatus.OK,
        detail=f"试用期工资为约定工资的 {ratio}%，不低于 80% / "
        f"Probation pay is {ratio}% of the agreed wage, at or above 80%.",
        quote=_excerpt(text, needle),
    )


def check_noncompete(text: str, lang: str) -> StatuteCheck:
    """Non-compete must stay within 2 years and carry compensation (LCL art. 23/24)."""
    basis = "《劳动合同法》第二十三、二十四条 / PRC Labor Contract Law, Arts. 23-24"
    anchor = re.search(r"竞业限制|竞业禁止|[Nn]on-?compete", text)
    if not anchor:
        return StatuteCheck(
            rule_id="cn_noncompete_term_and_compensation",
            title="竞业限制期限与补偿 / Non-compete term & compensation",
            basis=basis,
            status=StatuteStatus.UNKNOWN,
            detail="未发现竞业限制条款 / No non-compete clause found.",
        )
    years, years_quote = _search_number(
        [r"竞业[限禁]制[^。；;]{0,20}?([0-9]+|[一二两三四五六七八九十]+)\s*年"], text
    )
    months, months_quote = _search_number(
        [
            r"竞业[限禁]制[^。；;]{0,20}?([0-9]+|[一二两三四五六七八九十]+)\s*个?月",
            r"[Nn]on-?compete[^.]{0,40}?([0-9]+)\s*(?:years?|months?)",
        ],
        text,
    )
    term_months = years * 12 if years is not None else months
    quote = _excerpt(text, years_quote or months_quote or anchor.group(0))
    has_compensation = bool(
        re.search(r"竞业[限禁][^。]{0,80}?补偿|补偿[^。]{0,40}竞业|每月补偿|经济补偿", text)
    )
    if term_months is not None and term_months > 24:
        return StatuteCheck(
            rule_id="cn_noncompete_term_and_compensation",
            title="竞业限制期限与补偿 / Non-compete term & compensation",
            basis=basis,
            status=StatuteStatus.VIOLATION,
            detail=f"竞业限制期限 {term_months} 个月超过法定 2 年上限 / "
            f"Non-compete term of {term_months} months exceeds the 2-year cap.",
            quote=quote,
        )
    if not has_compensation:
        return StatuteCheck(
            rule_id="cn_noncompete_term_and_compensation",
            title="竞业限制期限与补偿 / Non-compete term & compensation",
            basis=basis,
            status=StatuteStatus.VIOLATION,
            detail="约定了竞业限制义务，但全文未见按月经济补偿，条款效力存疑 / "
            "A non-compete duty is imposed but no monthly compensation appears anywhere.",
            quote=quote,
        )
    if term_months is None:
        return StatuteCheck(
            rule_id="cn_noncompete_term_and_compensation",
            title="竞业限制期限与补偿 / Non-compete term & compensation",
            basis=basis,
            status=StatuteStatus.UNKNOWN,
            detail="有竞业限制与补偿安排，但期限无法解析 / "
            "Non-compete with compensation found, but the term is unparseable.",
            quote=quote,
        )
    return StatuteCheck(
        rule_id="cn_noncompete_term_and_compensation",
        title="竞业限制期限与补偿 / Non-compete term & compensation",
        basis=basis,
        status=StatuteStatus.OK,
        detail=f"竞业限制 {term_months} 个月且有经济补偿，符合 2 年上限 / "
        f"Non-compete of {term_months} months with compensation, within the 2-year cap.",
        quote=quote,
    )


def check_penalty_scope(text: str, lang: str) -> StatuteCheck:
    """Worker penalties are only lawful for training service periods and
    non-competes; anything broader is void (LCL art. 22, 23, 25)."""
    basis = "《劳动合同法》第二十二、二十三、二十五条 / PRC Labor Contract Law, Arts. 22-25"
    sentences = re.split(r"(?<=[。；;.!？?])\s*", text)
    allowed = ("培训", "服务期", "竞业", "training", "non-?compete")
    offenders: list[str] = []
    for sentence in sentences:
        if "违约金" not in sentence and "liquidated damages" not in sentence.lower():
            continue
        window = sentence
        if not any(re.search(anchor, window, re.IGNORECASE) for anchor in allowed):
            offenders.append(sentence.strip())
    if offenders:
        return StatuteCheck(
            rule_id="cn_penalty_scope_limit",
            title="违约金适用范围 / Penalty scope",
            basis=basis,
            status=StatuteStatus.VIOLATION,
            detail=f"发现 {len(offenders)} 处与培训服务期或竞业限制无关的违约金约定，依法无效 / "
            f"Found {len(offenders)} penalty clause(s) untied to training or non-compete, void by law.",
            quote=offenders[0][:120],
        )
    if re.search(r"违约金|liquidated damages", text, re.IGNORECASE):
        return StatuteCheck(
            rule_id="cn_penalty_scope_limit",
            title="违约金适用范围 / Penalty scope",
            basis=basis,
            status=StatuteStatus.OK,
            detail="违约金均挂在培训服务期或竞业限制语境下，未越界 / "
            "Penalty clauses are all anchored to training or non-compete contexts.",
            quote=_excerpt(text, "违约金"),
        )
    return StatuteCheck(
        rule_id="cn_penalty_scope_limit",
        title="违约金适用范围 / Penalty scope",
        basis=basis,
        status=StatuteStatus.UNKNOWN,
        detail="未发现违约金条款 / No penalty clause found.",
    )


def check_earnest_money(text: str, lang: str) -> StatuteCheck:
    """Earnest money (定金) must not exceed 20% of the contract value
    (Civil Code art. 586)."""
    basis = "《民法典》第五百八十六条 / PRC Civil Code, Art. 586"
    deposit_m = re.search(r"定金[^。；;]{0,12}?([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:元|块)", text)
    if not deposit_m:
        return StatuteCheck(
            rule_id="cn_earnest_money_cap",
            title="定金比例上限 / Earnest-money cap",
            basis=basis,
            status=StatuteStatus.UNKNOWN,
            detail="未发现明确定金金额（押金不在本条约束范围）/ "
            "No explicit earnest-money amount found (ordinary deposits are outside this rule).",
        )
    deposit = float(deposit_m.group(1).replace(",", ""))
    total_m = re.search(r"(?:合同总金额|合同总额|租金总额)[^。；;]{0,10}?([0-9][0-9,]*(?:\.[0-9]+)?)\s*元", text)
    if not total_m:
        rent_m = re.search(r"(?:月租金|租金)[^。；;]{0,10}?([0-9][0-9,]*(?:\.[0-9]+)?)\s*元", text)
        months, _ = _search_number(_CONTRACT_MONTHS_ONLY, text)
        years, _ = _search_number(_CONTRACT_YEARS, text)
        term = years * 12 if years is not None else months
        if rent_m and term:
            total = float(rent_m.group(1).replace(",", "")) * term
        else:
            return StatuteCheck(
                rule_id="cn_earnest_money_cap",
                title="定金比例上限 / Earnest-money cap",
                basis=basis,
                status=StatuteStatus.UNKNOWN,
                detail=f"定金 {deposit:,.0f} 元，但合同总额无法推算 / "
                f"Earnest money is {deposit:,.0f}, but the contract total cannot be derived.",
                quote=_excerpt(text, deposit_m.group(0)),
            )
    else:
        total = float(total_m.group(1).replace(",", ""))
    cap = total * 0.2
    if deposit > cap:
        return StatuteCheck(
            rule_id="cn_earnest_money_cap",
            title="定金比例上限 / Earnest-money cap",
            basis=basis,
            status=StatuteStatus.VIOLATION,
            detail=f"定金 {deposit:,.0f} 元超出合同总额 20%（{cap:,.0f} 元），超出部分无效 / "
            f"Earnest money {deposit:,.0f} exceeds 20% of the contract value ({cap:,.0f}); the excess is void.",
            quote=_excerpt(text, deposit_m.group(0)),
        )
    return StatuteCheck(
        rule_id="cn_earnest_money_cap",
        title="定金比例上限 / Earnest-money cap",
        basis=basis,
        status=StatuteStatus.OK,
        detail=f"定金 {deposit:,.0f} 元未超合同总额 20% / "
        f"Earnest money {deposit:,.0f} stays within 20% of the contract value.",
        quote=_excerpt(text, deposit_m.group(0)),
    )


def check_lease_term(text: str, lang: str) -> StatuteCheck:
    """A lease term may not exceed 20 years (Civil Code art. 705)."""
    basis = "《民法典》第七百零五条 / PRC Civil Code, Art. 705"
    years, years_quote = _search_number(
        [
            r"租赁期限[^。；;]{0,12}?([0-9]+|[一二两三四五六七八九十]+)\s*年",
            r"[Ll]ease term[^.]{0,30}?([0-9]+)\s*years?",
        ],
        text,
    )
    if years is None:
        return StatuteCheck(
            rule_id="cn_lease_term_cap",
            title="租赁期限上限 / Lease-term cap",
            basis=basis,
            status=StatuteStatus.UNKNOWN,
            detail="未找到明确的租赁年限 / No explicit lease term in years found.",
        )
    if years > 20:
        return StatuteCheck(
            rule_id="cn_lease_term_cap",
            title="租赁期限上限 / Lease-term cap",
            basis=basis,
            status=StatuteStatus.VIOLATION,
            detail=f"租赁期限 {years} 年超过 20 年上限，超出部分无效 / "
            f"Lease term of {years} years exceeds the 20-year cap; the excess is void.",
            quote=_excerpt(text, years_quote),
        )
    return StatuteCheck(
        rule_id="cn_lease_term_cap",
        title="租赁期限上限 / Lease-term cap",
        basis=basis,
        status=StatuteStatus.OK,
        detail=f"租赁期限 {years} 年在 20 年上限之内 / "
        f"Lease term of {years} years is within the 20-year cap.",
        quote=_excerpt(text, years_quote),
    )


_EMPLOYMENT_RULES = [
    check_probation_duration,
    check_probation_wage,
    check_noncompete,
    check_penalty_scope,
]
_LEASE_RULES = [check_earnest_money, check_lease_term]

_EMPLOYMENT_HINTS = ("劳动", "聘用", "雇佣", "employ", "probation", "试用期")
_LEASE_HINTS = ("租赁", "出租", "承租", "lease", "rent", "tenan")


def run_checklist(contract_text: str, contract_type: str = "unknown", lang: str = "zh") -> list[StatuteCheck]:
    """Evaluate every applicable statute rule against the contract text.

    When the type is known, only that type's rules run. When it is not,
    rules self-select by topic hints in the text, so an unclassified
    employment contract still gets its probation checked.
    """
    text_l = contract_text.lower()
    employment = contract_type == "employment" or (
        contract_type == "unknown" and any(h in text_l or h in contract_text for h in _EMPLOYMENT_HINTS)
    )
    lease = contract_type == "lease" or (
        contract_type == "unknown" and any(h in text_l or h in contract_text for h in _LEASE_HINTS)
    )
    checks: list[StatuteCheck] = []
    if employment:
        checks.extend(rule(contract_text, lang) for rule in _EMPLOYMENT_RULES)
    if lease:
        checks.extend(rule(contract_text, lang) for rule in _LEASE_RULES)
    return checks
