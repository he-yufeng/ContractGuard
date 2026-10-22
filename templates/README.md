# Contract templates

Ready-to-use contract starters for the most common situations, each with an
inline usage note and a "常见坑" (common red flags) appendix explaining the
specific traps the clause wording is designed to avoid. They pair with the
deterministic statute checks: the same red flags these templates warn about
are the ones `contractguard scan` looks for in contracts you receive.

| Template | Scenario | Watch-list highlights |
|----------|----------|------------------------|
| `loan_cn.txt` | 民间借贷（个人对个人借款） | 砍头息按实际交付认定本金；借期与逾期利率都受 LPR 四倍上限；大额务必银行转账留凭证；复利条款绕不过上限 |
| `nda_cn.txt` | 商业合作 / 尽调 / 技术交流的双向保密 | 保密期限别写「永久」；天价违约金会被酌减；竞业限制混不进保密协议；例外情形和人员范围必须封口 |
| `freelance_cn.txt` | 软件开发/设计/咨询承揽（自由职业接单） | 中途解除的法定补偿写双向对等；「验收合格才付款」必须配验收期限否则无限压款；背景 IP 与署名权不能概括让渡 |

More templates land as the deterministic rule families grow (the corpus in
`corpus/` pins each family's verdicts on hostile and clean samples first, so a
template only ships once its watch list is machine-checkable).

These templates are starting points, not legal advice. Significant contracts
should still go to a qualified lawyer in your jurisdiction.
