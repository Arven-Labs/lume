from datetime import date

from pydantic import BaseModel


class TaxRule(BaseModel):
    key: str
    value: float
    effective_from: date
    description: str
    source: str
    verified_at: date


class TaxRulesResponse(BaseModel):
    jurisdiction: str
    rules: list[TaxRule]
