"""Disclaimer and coverage boundaries, one source of truth.

Every user-facing surface (web home, HTML/PDF footer, markdown report) reads
these strings so the wording can never drift between pages. Saying plainly
what the tool is not, and which jurisdictions are actually audited, is what
makes the rest of the output trustworthy.
"""

DISCLAIMER = {
    "en": "ContractGuard is not legal advice. It flags patterns worth a second look; a qualified lawyer makes the call.",
    "zh": "ContractGuard 不构成法律意见。它标出值得多看一眼的风险点，最终判断请咨询专业律师。",
}

SCOPE_NOTE = {
    "en": "Audited scope today: California residential leases and PRC employment/labor contracts. Other jurisdictions are not verified yet.",
    "zh": "当前核查范围：加州住宅租赁与中国劳动/劳务合同。其他法域暂未核验，结果仅供参考。",
}

HOME_MD_EN = (
    "# ContractGuard\n\n"
    "Upload a contract and get an instant AI review with red flags, "
    "warnings, protections, statute checks, and a fairness score.\n\n"
    f"*{DISCLAIMER['en']}*\n\n"
    f"*{SCOPE_NOTE['en']}*"
)

HOME_MD_ZH = (
    "# ContractGuard\n\n"
    "上传合同，即刻获得 AI 审查：红线条款、警告、保护条款、法条核查和公允评分。\n\n"
    f"*{DISCLAIMER['zh']}*\n\n"
    f"*{SCOPE_NOTE['zh']}*"
)
