from backend.agent.nodes.risk import evaluate_risk_rules


def _valid_payload() -> dict:
    return {
        "type": "scope_change",
        "confidence": 0.9,
        "affects_deliverable": "D1",
        "detail": "Client asked for additional export variants.",
        "explicitly_excluded": False,
        "new_deliverable": False,
        "effort_delta_hours": 4,
        "dollar_impact": 300,
        "risk_level": "low",
        "recommended_action": "auto_approve",
        "reasoning": "The request is minor and within expected contingency.",
    }


def test_unresolved_routing_forces_flag() -> None:
    decision = evaluate_risk_rules(_valid_payload(), routing_status="needs_routing")
    assert decision.final_action == "flag_for_pm"
    assert "unresolved_project_mapping" in decision.reason_codes


def test_low_confidence_forces_flag() -> None:
    payload = _valid_payload()
    payload["confidence"] = 0.5
    decision = evaluate_risk_rules(payload)
    assert decision.final_action == "flag_for_pm"
    assert "low_confidence" in decision.reason_codes


def test_clarification_ignored() -> None:
    payload = _valid_payload()
    payload["type"] = "clarification"
    decision = evaluate_risk_rules(payload)
    assert decision.final_action == "ignore"


def test_high_dollar_impact_forces_flag() -> None:
    payload = _valid_payload()
    payload["dollar_impact"] = 6000
    decision = evaluate_risk_rules(payload)
    assert decision.final_action == "flag_for_pm"
    assert "high_dollar_impact" in decision.reason_codes
