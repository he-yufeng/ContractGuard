"""Official source links for each statute rule, keyed by rule_id.

Every verdict a user sees carries a legal basis; this map makes that basis
clickable so nobody has to take the citation on faith. Links were verified
reachable when added (CA: leginfo.legislature.ca.gov section pages; PRC:
gov.cn gazette pages where a full-text page exists, otherwise the national
statute database front page which searches the current consolidated text).
"""

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
    # no stable gov.cn full-text page for the Labour Law; the national
    # database front page searches the current consolidated text
    "cn_overtime_pay_floor": FLK_HOME,
    "cn_social_insurance_waiver": FLK_HOME,
}


def reference_for(rule_id: str) -> str:
    """Official source URL for a rule, or "" when none is known."""
    return RULE_REFERENCES.get(rule_id, "")
