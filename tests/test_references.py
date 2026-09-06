"""Every statute verdict must carry a reachable-looking official reference."""

from contractguard.checklist import run_checklist
from contractguard.html import generate_html_report
from contractguard.models import AnalysisResult, ContractType
from contractguard.references import RULE_REFERENCES, reference_for

# fixtures trip both engines: a CA lease over the deposit cap, and a CN
# employment text over the probation cap plus lease-style clauses
CA_TEXT = (
    "Governing law: California. The premises are in Los Angeles, CA. "
    "Monthly rent is $2,000. Tenant shall pay a security deposit of $5,000. "
    "Landlord may enter the premises at any time without notice. "
    "The deposit is refundable within 30 days."
)
CN_TEXT = (
    "本合同受中华人民共和国法律管辖。劳动合同期限三年，试用期十二个月。"
    "试用期工资为约定工资的百分之五十。竞业限制期限五年，无补偿。"
    "定金为合同总价款的百分之五十。租赁期限三十年。"
    "工作日加班工资按百分之一百二十支付。员工自愿放弃社会保险。"
)


def _all_checks():
    ca = run_checklist(CA_TEXT, contract_type="lease", lang="en", jurisdiction="us-ca")
    cn = run_checklist(CN_TEXT, contract_type="unknown", lang="zh", jurisdiction="cn")
    return list(ca) + list(cn)


def test_every_returned_rule_has_a_reference():
    checks = _all_checks()
    assert checks, "fixtures should produce verdicts"
    missing = [c.rule_id for c in checks if not reference_for(c.rule_id)]
    assert not missing, f"rules missing an official reference: {missing}"


def test_references_look_like_official_urls():
    for rule_id, url in RULE_REFERENCES.items():
        assert url.startswith("https://"), rule_id
        host = url.split("/")[2]
        assert host.endswith("ca.gov") or host.endswith("gov.cn") or host == "flk.npc.gov.cn", rule_id


def test_html_report_links_the_basis():
    result = AnalysisResult(
        contract_type=ContractType.EMPLOYMENT,
        summary="fixture",
        parties=[],
        key_terms=[],
        red_flags=[],
        warnings=[],
        good_clauses=[],
        fairness_score=50,
        fairness_grade="C",
    )
    result.statute_checks = run_checklist(CN_TEXT, "unknown", "zh")
    html = generate_html_report(result, lang="zh")
    assert "gov.cn" in html or "flk.npc.gov.cn" in html
    assert 'target="_blank"' in html
