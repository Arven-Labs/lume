"""Regras de imposto sobre investimentos (pessoa física, Brasil).

Não existe fonte oficial legível por máquina pra alíquotas/limites — este módulo É a fonte:
dado curado à mão, versionado no repo, com a fonte e a data de verificação de cada valor. Mantido
aqui (e não num .json) pra entrar no binário do sidecar sem configuração extra de empacotamento.

Cada regra vale a partir de `effective_from`; mudança de lei = nova entrada com a data nova, nunca
editar a antiga (o consumidor apura meses passados com a regra vigente na época). Primeiro
consumidor: Fase 24 do Anchor (apuração de IR em renda variável).
"""

from datetime import date

from app.schemas.tax_rules import TaxRule

_RECEITA_BOLSA = (
    "https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/"
    "renda-variavel/bolsa-de-valores-1"
)
_RECEITA_CALCULO = f"{_RECEITA_BOLSA}/calculo-e-pagamento-do-imposto"
_RECEITA_ISENCOES = f"{_RECEITA_BOLSA}/isencoes"
_RECEITA_REVAR = (
    "https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/"
    "renda-variavel/manual"
)
_VERIFIED = date(2026, 10, 14)

TAX_RULES_BR: list[TaxRule] = [
    TaxRule(
        key="common_rate",
        value=0.15,
        effective_from=date(2005, 1, 1),
        description="Rate on monthly net gains from regular (swing) trades of stocks, units, "
        "ETFs and BDRs on B3",
        source=_RECEITA_BOLSA,
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="day_trade_rate",
        value=0.20,
        effective_from=date(2005, 1, 1),
        description="Rate on monthly net gains from day trades on B3",
        source=_RECEITA_BOLSA,
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="fii_rate",
        value=0.20,
        effective_from=date(2005, 1, 1),
        description="Rate on net gains from selling real estate fund (FII/Fiagro) quotas, "
        "regular or day trade",
        source=_RECEITA_REVAR,
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="stock_exemption_monthly_sales",
        value=20000.0,
        effective_from=date(2005, 1, 1),
        description="Monthly stock sales up to this amount make stock gains exempt (stocks "
        "only; not units — SC Cosit 145/2021 —, ETFs, BDRs, FIIs or day trade)",
        source=_RECEITA_ISENCOES,
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="irrf_common_rate",
        value=0.00005,
        effective_from=date(2005, 1, 1),
        description="Withholding on the sale value of regular trades (0.005%), deductible "
        "from the tax due",
        source=_RECEITA_CALCULO,
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="irrf_day_trade_rate",
        value=0.01,
        effective_from=date(2005, 1, 1),
        description="Withholding on day trade gains (1%), deductible from the tax due",
        source="Lei 9.430/1996, art. 8º (verify on planalto.gov.br)",
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="darf_minimum",
        value=10.0,
        effective_from=date(2005, 1, 1),
        description="Tax below this amount is not paid that month; it accumulates into the "
        "following months",
        source=_RECEITA_REVAR,
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="darf_code_b3",
        value=6015,
        effective_from=date(2005, 1, 1),
        description="DARF revenue code for net gains on the stock exchange (individuals)",
        source=_RECEITA_CALCULO,
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="jcp_irrf_rate",
        value=0.15,
        effective_from=date(1996, 1, 1),
        description="Withholding on interest on equity (JCP)",
        source="Lei 9.249/1995, art. 9º, § 2º",
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="jcp_irrf_rate",
        value=0.175,
        effective_from=date(2026, 1, 1),
        description="Withholding on interest on equity (JCP), raised by LC 224/2025",
        source="LC 224/2025 (secondary sources; verify on planalto.gov.br)",
        verified_at=_VERIFIED,
    ),
    TaxRule(
        key="crypto_exemption_monthly_sales",
        value=35000.0,
        effective_from=date(2019, 1, 1),
        description="Monthly crypto sales up to this amount make crypto gains exempt "
        "(domestic exchanges)",
        source="IN RFB 1.888/2019 (secondary sources; verify on gov.br)",
        verified_at=_VERIFIED,
    ),
]


def get_tax_rules_br() -> list[TaxRule]:
    return TAX_RULES_BR
