"""Official source links for each statute rule, keyed by rule_id.

Every verdict a user sees carries a legal basis; this map makes that basis
clickable so nobody has to take the citation on faith. Links were verified
reachable when added (CA: leginfo.legislature.ca.gov section pages; PRC:
gov.cn gazette pages where a full-text page exists, otherwise the national
statute database front page which searches the current consolidated text).
"""

from dataclasses import dataclass

LEGINFO = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum="
GOV_GAZETTE_LCL = "https://www.gov.cn/gongbao/content/2007/content_711013.htm"
GOV_CIVIL_CODE = "https://www.gov.cn/xinwen/2020-05/28/content_5515756.htm"
FLK_HOME = "https://flk.npc.gov.cn/"

RULE_REFERENCES: dict[str, str] = {
    "us_ca_security_deposit_cap": LEGINFO + "1950.5",
    "us_ca_deposit_refundability": LEGINFO + "1950.5",
    "us_ca_entry_notice": LEGINFO + "1954",
    "us_ca_deposit_return_deadline": LEGINFO + "1950.5",
    "cn_probation_duration_cap": GOV_GAZETTE_LCL,
    "cn_probation_wage_floor": GOV_GAZETTE_LCL,
    "cn_noncompete_term_and_compensation": GOV_GAZETTE_LCL,
    "cn_penalty_scope_limit": GOV_GAZETTE_LCL,
    "cn_training_penalty_cap": GOV_GAZETTE_LCL,
    "cn_earnest_money_cap": GOV_CIVIL_CODE,
    "cn_lease_term_cap": GOV_CIVIL_CODE,
    "cn_loan_no_prededucted_interest": GOV_CIVIL_CODE,
    # 民间借贷司法解释无稳定 gov.cn 全文页；国家法律法规数据库可检索现行文本
    "cn_loan_interest_cap": FLK_HOME,
    # no stable gov.cn full-text page for the Labour Law; the national
    # database front page searches the current consolidated text
    "cn_overtime_pay_floor": FLK_HOME,
    "cn_social_insurance_waiver": FLK_HOME,
}


def reference_for(rule_id: str) -> str:
    """Official source URL for a rule, or "" when none is known."""
    return RULE_REFERENCES.get(rule_id, "")


@dataclass(frozen=True)
class StatuteAudit:
    """Human-review record tying a rule's behavior to the statute text.

    `excerpt` summarizes the controlling text in the rule's own language;
    `checked_points` lists the numeric/threshold claims the rule relies on.
    The audit test suite drives each rule across its claimed threshold and
    pins the verdict flip, so a code constant drifting from the statute fails.
    """

    rule_id: str
    excerpt: str
    checked_points: tuple[str, ...]


STATUTE_AUDIT: dict[str, StatuteAudit] = {
    "us_ca_security_deposit_cap": StatuteAudit(
        rule_id="us_ca_security_deposit_cap",
        excerpt=(
            "Civil Code §1950.5 (as amended by AB 12, eff. 2024-07-01): "
            "a residential security deposit may not exceed one month's rent, "
            "furnished or unfurnished (narrow small-landlord exceptions aside)."
        ),
        checked_points=("cap = 1 month's rent", "violation strictly above the cap"),
    ),
    "us_ca_deposit_refundability": StatuteAudit(
        rule_id="us_ca_deposit_refundability",
        excerpt=(
            "Civil Code §1950.5: all residential deposits are refundable; a "
            "'non-refundable security deposit' is void as a matter of law."
        ),
        checked_points=("any non-refundable deposit clause is a violation",),
    ),
    "us_ca_entry_notice": StatuteAudit(
        rule_id="us_ca_entry_notice",
        excerpt=(
            "Civil Code §1954: entry requires reasonable advance notice, "
            "presumed to be 24 hours in writing; 'at any time without notice' "
            "is void."
        ),
        checked_points=("24-hour written notice presumed floor",),
    ),
    "us_ca_deposit_return_deadline": StatuteAudit(
        rule_id="us_ca_deposit_return_deadline",
        excerpt=(
            "Civil Code §1950.5(g): within 21 days after the tenant vacates, "
            "the landlord must return the deposit balance with an itemized "
            "statement of deductions."
        ),
        checked_points=("deadline = 21 days after move-out", "violation strictly above 21"),
    ),
    "cn_probation_duration_cap": StatuteAudit(
        rule_id="cn_probation_duration_cap",
        excerpt=(
            "《劳动合同法》第十九条：不满三个月或以完成任务为期限不得约定试用期；"
            "三个月以上不满一年试用期不得超过一个月；一年以上不满三年不得超过二个月；"
            "三年以上固定期限和无固定期限不得超过六个月。"
        ),
        checked_points=("<3mo → 0", "3mo-1yr → ≤1", "1-3yr → ≤2", "≥3yr/open → ≤6"),
    ),
    "cn_probation_wage_floor": StatuteAudit(
        rule_id="cn_probation_wage_floor",
        excerpt=("《劳动合同法》第二十条：试用期工资不得低于约定工资的百分之八十，并不得低于当地最低工资标准。"),
        checked_points=("floor = 80% of the agreed wage",),
    ),
    "cn_noncompete_term_and_compensation": StatuteAudit(
        rule_id="cn_noncompete_term_and_compensation",
        excerpt=("《劳动合同法》第二十三、二十四条：竞业限制须支付经济补偿，期限不得超过二年。"),
        checked_points=("term ≤ 2 years", "compensation required during the term"),
    ),
    "cn_penalty_scope_limit": StatuteAudit(
        rule_id="cn_penalty_scope_limit",
        excerpt=(
            "《劳动合同法》第二十二、二十三、二十五条：违约金仅得约定于专项培训服务期"
            "与竞业限制两种情形，其他一律不得约定由劳动者承担违约金。"
        ),
        checked_points=("liquidated damages only for training-service or non-compete",),
    ),
    "cn_training_penalty_cap": StatuteAudit(
        rule_id="cn_training_penalty_cap",
        excerpt=("《劳动合同法》第二十二条：专项培训服务期违约金不得超过未履行部分所应分摊的培训费用。"),
        checked_points=("penalty ≤ unamortized training cost",),
    ),
    "cn_earnest_money_cap": StatuteAudit(
        rule_id="cn_earnest_money_cap",
        excerpt=("《民法典》第五百八十六条：定金数额不得超过主合同标的额的百分之二十，超过部分不产生定金的效力。"),
        checked_points=("earnest money ≤ 20% of the contract value",),
    ),
    "cn_lease_term_cap": StatuteAudit(
        rule_id="cn_lease_term_cap",
        excerpt=("《民法典》第七百零五条：租赁期限不得超过二十年，超过部分无效。"),
        checked_points=("lease term ≤ 20 years",),
    ),
    "cn_loan_interest_cap": StatuteAudit(
        rule_id="cn_loan_interest_cap",
        excerpt=(
            "最高法《关于审理民间借贷案件适用法律若干问题的规定》第二十五条："
            "出借人请求按约定利率支付利息的，法院支持的利率以合同成立时一年期"
            "贷款市场报价利率四倍为限。当前一年期 LPR 为 3.0%（2026-08 报价），"
            "对应上限约 12.0%；该值随 LPR 浮动。"
        ),
        checked_points=(
            "annualized rate ≤ 4x the 1-year LPR at signing",
            "reference LPR 3.0% (2026-08) -> cap 12.0%",
        ),
    ),
    "cn_loan_no_prededucted_interest": StatuteAudit(
        rule_id="cn_loan_no_prededucted_interest",
        excerpt=(
            "《民法典》第六百七十条：借款的利息不得预先在本金中扣除；"
            "预先扣除的，按照实际借款数额返还借款并计算利息。"
        ),
        checked_points=("no interest pre-deducted from principal",),
    ),
    "cn_overtime_pay_floor": StatuteAudit(
        rule_id="cn_overtime_pay_floor",
        excerpt=(
            "《劳动法》第四十四条：工作日加班不低于工资的百分之一百五十，"
            "休息日不低于百分之二百，法定休假日不低于百分之三百。"
        ),
        checked_points=("150% / 200% / 300% floors",),
    ),
    "cn_social_insurance_waiver": StatuteAudit(
        rule_id="cn_social_insurance_waiver",
        excerpt=(
            "《劳动法》第七十二条 + 《劳动合同法》第二十六条：用人单位和劳动者必须"
            "依法参加社会保险；以现金替代或约定放弃社保的条款无效。"
        ),
        checked_points=("waiver/cash-substitute clauses are void",),
    ),
}
