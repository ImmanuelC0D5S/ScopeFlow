"""Diff node - compare extracted intent vs baseline."""
from typing import Optional


def diff_against_baseline(extracted: dict, baseline: dict) -> dict:
    """
    Compare extracted scope change against baseline.
    
    This adds additional context and validation to the extracted data.
    
    Args:
        extracted: Extracted scope change data from LLM
        baseline: Project baseline with deliverables and exclusions
        
    Returns:
        Enhanced extracted data with diff information
    """
    # Make a copy to avoid modifying original
    result = extracted.copy()
    
    # Validate deliverable code exists in baseline
    affects_deliverable = extracted.get("affects_deliverable")
    if affects_deliverable:
        deliverable_codes = [
            d.get("code") for d in baseline.get("deliverables", [])
        ]
        
        if affects_deliverable not in deliverable_codes:
            result["validation_warnings"] = result.get("validation_warnings", [])
            result["validation_warnings"].append(
                f"Deliverable code '{affects_deliverable}' not found in baseline"
            )
            # Set to None if invalid
            result["affects_deliverable"] = None
    
    # Check if request matches any exclusion
    detail = extracted.get("detail", "").lower()
    exclusions = baseline.get("exclusions", [])
    
    matching_exclusions = []
    for exclusion in exclusions:
        if any(word in detail for word in exclusion.lower().split()):
            matching_exclusions.append(exclusion)
    
    if matching_exclusions:
        result["matching_exclusions"] = matching_exclusions
        # If LLM didn't catch it, flag it
        if not extracted.get("explicitly_excluded"):
            result["explicitly_excluded"] = True
            result["validation_warnings"] = result.get("validation_warnings", [])
            result["validation_warnings"].append(
                "Matched exclusions that LLM may have missed"
            )
    
    # Calculate impact relative to total contract value
    dollar_impact = extracted.get("dollar_impact")
    total_value = baseline.get("total_contract_value", 0)
    
    if dollar_impact and total_value > 0:
        impact_percentage = (dollar_impact / total_value) * 100
        result["impact_percentage"] = round(impact_percentage, 2)
        
        # Escalate if impact is significant
        if impact_percentage > 10:
            result["high_impact_flag"] = True
    
    # Add baseline context
    result["baseline_summary"] = {
        "total_deliverables": len(baseline.get("deliverables", [])),
        "total_exclusions": len(baseline.get("exclusions", [])),
        "total_contract_value": total_value,
        "currency": baseline.get("currency", "USD")
    }
    
    return result


def validate_extraction(extracted: dict) -> tuple[bool, list[str]]:
    """
    Validate that extracted data has required fields.
    
    Args:
        extracted: Extracted scope change data
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    required_fields = [
        "type",
        "confidence",
        "detail",
        "explicitly_excluded",
        "new_deliverable",
        "risk_level",
        "recommended_action",
        "reasoning"
    ]
    
    errors = []
    
    for field in required_fields:
        if field not in extracted:
            errors.append(f"Missing required field: {field}")
    
    # Validate types
    if "confidence" in extracted:
        confidence = extracted["confidence"]
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            errors.append("Confidence must be a number between 0 and 1")
    
    if "type" in extracted:
        valid_types = ["scope_change", "clarification", "admin", "ambiguous"]
        if extracted["type"] not in valid_types:
            errors.append(f"Invalid type: {extracted['type']}")
    
    if "risk_level" in extracted:
        valid_levels = ["low", "medium", "high"]
        if extracted["risk_level"] not in valid_levels:
            errors.append(f"Invalid risk_level: {extracted['risk_level']}")
    
    if "recommended_action" in extracted:
        valid_actions = ["auto_approve", "flag_for_pm", "ignore"]
        if extracted["recommended_action"] not in valid_actions:
            errors.append(f"Invalid recommended_action: {extracted['recommended_action']}")
    
    return (len(errors) == 0, errors)

# Made with Bob
