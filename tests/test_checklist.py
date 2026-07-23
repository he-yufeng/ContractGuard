"""Tests for the deterministic statute checklist."""

from __future__ import annotations

from contractguard.checklist import run_checklist
from contractguard.models import AnalysisResult, ContractType, StatuteStatus


def _checks(text: str, contract_type: str = "employment", lang: str = "zh"):
    return {c.rule_id: c for c in run_checklist(text, contract_type, lang)}


def _result_with_checks(text: str) -> AnalysisResult:
    result = AnalysisResult(
        contract_type=ContractType.EMPLOYMENT,
        summary="s",
        fairness_score=50,
        fairness_grade="C",
    )
    result.statute_checks = run_checklist(text, "employment", "zh")
    return result


# ---------------------------------------------------------------------------
# Probation duration cap (LCL art. 19)
# ---------------------------------------------------------------------------


def test_probation_over_cap_is_violation():
    text = "劳动合同期限三年，试用期八个月，月工资一万元。"
    check = _checks(text)["cn_probation_duration_cap"]
    assert check.status == StatuteStatus.VIOLATION
    assert "6" in check.detail


def test_probation_within_cap_is_ok():
    text = "劳动合同期限三年，试用期六个月，月工资一万元。"
    check = _checks(text)["cn_probation_duration_cap"]
    assert check.status == StatuteStatus.OK


def test_probation_on_short_term_is_violation():
    text = "本合同期限二个月，试用期一个月。"
    check = _checks(text)["cn_probation_duration_cap"]
    assert check.status == StatuteStatus.VIOLATION
    assert "不得约定试用期" in check.detail


def test_probation_unknown_when_no_clause():
    text = "劳动合同期限三年，月工资一万元。"
    check = _checks(text)["cn_probation_duration_cap"]
    assert check.status == StatuteStatus.UNKNOWN


def test_probation_not_misread_as_term():
    # 试用期六个月 must not be parsed as the contract term.
    text = "劳动合同期限三年，试用期六个月。"
    check = _checks(text)["cn_probation_duration_cap"]
    assert check.status == StatuteStatus.OK


# ---------------------------------------------------------------------------
# Probation wage floor (LCL art. 20)
# ---------------------------------------------------------------------------


def test_probation_wage_below_floor_is_violation():
    check = _checks("试用期六个月，试用期工资为转正工资的 60%。")["cn_probation_wage_floor"]
    assert check.status == StatuteStatus.VIOLATION
    assert "60%" in check.detail


def test_probation_wage_at_floor_is_ok():
    check = _checks("试用期六个月，试用期工资为转正工资的 80%。")["cn_probation_wage_floor"]
    assert check.status == StatuteStatus.OK


# ---------------------------------------------------------------------------
# Non-compete (LCL art. 23/24)
# ---------------------------------------------------------------------------


def test_noncompete_over_two_years_is_violation():
    check = _checks("竞业限制期限为三年，公司每月支付经济补偿 3000 元。")[
        "cn_noncompete_term_and_compensation"
    ]
    assert check.status == StatuteStatus.VIOLATION


def test_noncompete_without_compensation_is_violation():
    check = _checks("离职后一年内不得从事同行业工作，竞业限制期内应遵守保密义务。")[
        "cn_noncompete_term_and_compensation"
    ]
    assert check.status == StatuteStatus.VIOLATION
    assert "经济补偿" in check.detail or "compensation" in check.detail


def test_noncompete_compliant_is_ok():
    check = _checks("竞业限制期限一年，公司每月给予经济补偿 5000 元。")[
        "cn_noncompete_term_and_compensation"
    ]
    assert check.status == StatuteStatus.OK


# ---------------------------------------------------------------------------
# Penalty scope (LCL art. 22/23/25)
# ---------------------------------------------------------------------------


def test_penalty_untied_clause_is_violation():
    text = "劳动者提前离职的，应向公司支付违约金五万元。"
    check = _checks(text)["cn_penalty_scope_limit"]
    assert check.status == StatuteStatus.VIOLATION
    assert "五万元" in check.quote or "无效" in check.detail


def test_penalty_tied_to_training_is_ok():
    text = "公司提供专项培训，服务期三年；提前离职的，按未履行部分支付培训违约金。"
    check = _checks(text)["cn_penalty_scope_limit"]
    assert check.status == StatuteStatus.OK


def test_penalty_unknown_when_absent():
    check = _checks("劳动合同期限三年，月工资一万元。")["cn_penalty_scope_limit"]
    assert check.status == StatuteStatus.UNKNOWN


# ---------------------------------------------------------------------------
# Earnest money cap (Civil Code art. 586)
# ---------------------------------------------------------------------------


def test_earnest_money_over_cap_is_violation():
    text = "合同总金额 100000 元，承租方支付定金 30000 元。"
    check = _checks(text, "lease")["cn_earnest_money_cap"]
    assert check.status == StatuteStatus.VIOLATION


def test_earnest_money_within_cap_is_ok():
    text = "合同总金额 100000 元，承租方支付定金 10000 元。"
    check = _checks(text, "lease")["cn_earnest_money_cap"]
    assert check.status == StatuteStatus.OK


def test_earnest_money_derives_total_from_monthly_rent():
    text = "租赁期限一年，月租金 5000 元，定金 20000 元。"
    check = _checks(text, "lease")["cn_earnest_money_cap"]
    assert check.status == StatuteStatus.VIOLATION  # 20000 > 5000*12*0.2 = 12000


# ---------------------------------------------------------------------------
# Lease term cap (Civil Code art. 705)
# ---------------------------------------------------------------------------


def test_lease_term_over_20_years_is_violation():
    check = _checks("租赁期限二十五年，月租金 3000 元。", "lease")["cn_lease_term_cap"]
    assert check.status == StatuteStatus.VIOLATION


def test_lease_term_within_cap_is_ok():
    check = _checks("租赁期限五年，月租金 3000 元。", "lease")["cn_lease_term_cap"]
    assert check.status == StatuteStatus.OK


# ---------------------------------------------------------------------------
# Type self-selection and report plumbing
# ---------------------------------------------------------------------------


def test_unknown_type_self_selects_by_topic():
    checks = run_checklist("劳动合同期限三年，试用期八个月。", "unknown", "zh")
    rule_ids = {c.rule_id for c in checks}
    assert "cn_probation_duration_cap" in rule_ids
    assert "cn_lease_term_cap" not in rule_ids


def test_checks_flow_into_markdown_and_html():
    from contractguard.html import generate_html_report
    from contractguard.report import generate_markdown_report

    result = _result_with_checks("劳动合同期限三年，试用期八个月。")
    md = generate_markdown_report(result)
    html = generate_html_report(result)
    assert "## Statute Checks" in md
    assert "试用期上限" in md
    assert "Statute Checks" in html
    assert "VIOLATION" in html
