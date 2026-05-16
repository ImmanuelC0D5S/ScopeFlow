from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from backend.core.schemas import ScopeChangeExtraction


RULE_ENGINE_VERSION = "2026-05-15.v1"


@dataclass
class RiskDecision:
    final_action: str
    reason_codes: list[str]
    llm_recommended_action: str
    rule_engine_version: str = RULE_ENGINE_VERSION


def evaluate_risk_rules(
    extracted_payload: dict[str, Any], *,
    routing_status: str = "resolved",
) -> RiskDecision:
    if routing_status != "resolved":
        return RiskDecision(
            final_action="flag_for_pm",
            reason_codes=["unresolved_project_mapping"],
            llm_recommended_action="flag_for_pm",
        )

    try:
        extracted = ScopeChangeExtraction.model_validate(extracted_payload)
    except ValidationError:
        return RiskDecision(
            final_action="flag_for_pm",
            reason_codes=["invalid_llm_payload"],
            llm_recommended_action="flag_for_pm",
        )

    if extracted.type.value in ("clarification", "admin"):
        return RiskDecision(
            final_action="ignore",
            reason_codes=["non_scope_message"],
            llm_recommended_action=extracted.recommended_action.value,
        )

    if extracted.confidence < 0.75:
        return RiskDecision(
            final_action="flag_for_pm",
            reason_codes=["low_confidence"],
            llm_recommended_action=extracted.recommended_action.value,
        )

    if extracted.explicitly_excluded:
        return RiskDecision(
            final_action="flag_for_pm",
            reason_codes=["explicitly_excluded"],
            llm_recommended_action=extracted.recommended_action.value,
        )

    if extracted.new_deliverable:
        return RiskDecision(
            final_action="flag_for_pm",
            reason_codes=["new_deliverable"],
            llm_recommended_action=extracted.recommended_action.value,
        )

    if extracted.dollar_impact is not None and extracted.dollar_impact > 5000:
        return RiskDecision(
            final_action="flag_for_pm",
            reason_codes=["high_dollar_impact"],
            llm_recommended_action=extracted.recommended_action.value,
        )

    return RiskDecision(
        final_action="auto_approve",
        reason_codes=["low_risk_default"],
        llm_recommended_action=extracted.recommended_action.value,
    )


def apply_risk_rules(extracted: dict[str, Any]) -> str:
    decision = evaluate_risk_rules(extracted)
    return decision.final_action
