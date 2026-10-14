from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.schemas.tax_rules import TaxRulesResponse
from app.services.tax_rules_service import get_tax_rules_br

router = APIRouter(prefix="/v1/tax-rules", tags=["tax-rules"])


@router.get("/br", response_model=TaxRulesResponse)
def get_br_tax_rules(_: str = Depends(require_api_key)):
    return TaxRulesResponse(jurisdiction="BR", rules=get_tax_rules_br())
