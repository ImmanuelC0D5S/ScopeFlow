"""Route node - determine final action based on risk assessment."""
from backend.agent.nodes.risk import evaluate_risk_rules


def route_change(extracted: dict, routing_status: str = "resolved") -> dict:
    """
    Route the scope change based on risk rules.
    
    Args:
        extracted: Extracted and validated scope change data
        routing_status: Project routing status
        
    Returns:
        Dictionary with routing decision
    """
    # Apply risk rules
    decision = evaluate_risk_rules(extracted, routing_status=routing_status)
    
    return {
        "final_action": decision.final_action,
        "reason_codes": decision.reason_codes,
        "llm_recommended_action": decision.llm_recommended_action,
        "rule_engine_version": decision.rule_engine_version
    }


def should_auto_approve(routing_decision: dict) -> bool:
    """
    Check if the change should be auto-approved.
    
    Args:
        routing_decision: Decision from route_change
        
    Returns:
        True if should auto-approve, False otherwise
    """
    return routing_decision.get("final_action") == "auto_approve"


def should_flag_for_pm(routing_decision: dict) -> bool:
    """
    Check if the change should be flagged for PM review.
    
    Args:
        routing_decision: Decision from route_change
        
    Returns:
        True if should flag for PM, False otherwise
    """
    return routing_decision.get("final_action") == "flag_for_pm"


def should_ignore(routing_decision: dict) -> bool:
    """
    Check if the change should be ignored.
    
    Args:
        routing_decision: Decision from route_change
        
    Returns:
        True if should ignore, False otherwise
    """
    return routing_decision.get("final_action") == "ignore"

# Made with Bob
