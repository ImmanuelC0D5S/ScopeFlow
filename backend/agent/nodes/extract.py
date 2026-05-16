"""Extract node - scope change extraction using LLM."""
import json
from typing import Optional
import google.generativeai as genai
from backend.core.config import settings


SCOPE_CHANGE_PROMPT_TEMPLATE = """You are a scope change analyst for a professional services firm.
Your job is to read client communications and determine whether they contain a scope change, compared to the original agreed contract.

## Original Scope Baseline

DELIVERABLES:
{deliverables}

EXCLUSIONS:
{exclusions}

TOTAL CONTRACT VALUE: {total_value}

---

## New Client Communication

SOURCE: {source}
DATE: {date}
FROM: {sender}

MESSAGE:
{message_body}

---

## Instructions

Analyze the message against the original scope baseline and return JSON with the following fields:

{{
  "type": "scope_change" | "clarification" | "admin" | "ambiguous",
  "confidence": 0.0 to 1.0,
  "affects_deliverable": "<deliverable code or null>",
  "detail": "<one sentence describing what changed>",
  "explicitly_excluded": true | false,
  "new_deliverable": true | false,
  "effort_delta_hours": <number or null if unknown>,
  "dollar_impact": <number or null if unknown>,
  "risk_level": "low" | "medium" | "high",
  "recommended_action": "auto_approve" | "flag_for_pm" | "ignore",
  "reasoning": "<one sentence explaining your verdict>"
}}

RULES:
- If the message is just a question or status check, type = "clarification"
- If the message requests work that is in the exclusions list, set explicitly_excluded = true
- If confidence is below 0.75, always set recommended_action = "flag_for_pm"
- If dollar_impact is unknown but effort_delta_hours is known, leave dollar_impact null
- Never invent deliverable codes that are not in the baseline
- Never return anything outside the JSON object
"""


def extract_scope_change(
    message: str,
    baseline: dict,
    sender: str = "unknown",
    source: str = "email",
    date: str = "",
    gemini_api_key: Optional[str] = None
) -> dict:
    """
    Extract scope change information from a message using Gemini.
    
    Args:
        message: Client message text
        baseline: Project baseline with deliverables and exclusions
        sender: Message sender
        source: Message source (email, slack, etc.)
        date: Message date
        gemini_api_key: Optional API key
        
    Returns:
        Dictionary with extracted scope change data
    """
    api_key = gemini_api_key or getattr(settings, 'gemini_api_key', None)
    
    if not api_key:
        # Return a default response if no API key
        return {
            "type": "ambiguous",
            "confidence": 0.0,
            "affects_deliverable": None,
            "detail": "Unable to analyze - no API key configured",
            "explicitly_excluded": False,
            "new_deliverable": False,
            "effort_delta_hours": None,
            "dollar_impact": None,
            "risk_level": "high",
            "recommended_action": "flag_for_pm",
            "reasoning": "No LLM API key configured"
        }
    
    # Format deliverables
    deliverables_text = ""
    if baseline.get("deliverables"):
        for d in baseline["deliverables"]:
            deliverables_text += f"- {d.get('code', 'N/A')}: {d.get('description', 'N/A')}"
            if d.get('estimated_hours'):
                deliverables_text += f" | {d['estimated_hours']} hrs"
            if d.get('due_date'):
                deliverables_text += f" | due {d['due_date']}"
            deliverables_text += "\n"
    else:
        deliverables_text = "No deliverables defined"
    
    # Format exclusions
    exclusions_text = ""
    if baseline.get("exclusions"):
        for exc in baseline["exclusions"]:
            exclusions_text += f"- {exc}\n"
    else:
        exclusions_text = "No exclusions defined"
    
    # Get total value
    total_value = baseline.get("total_contract_value", 0)
    currency = baseline.get("currency", "USD")
    
    # Build prompt
    prompt = SCOPE_CHANGE_PROMPT_TEMPLATE.format(
        deliverables=deliverables_text,
        exclusions=exclusions_text,
        total_value=f"{currency} {total_value:,.2f}",
        source=source,
        date=date or "unknown",
        sender=sender,
        message_body=message
    )
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-002')
        
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0,
                'max_output_tokens': 2048,
            }
        )
        
        response_text = response.text
        
        # Try to parse JSON
        try:
            extracted = json.loads(response_text)
            return extracted
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                extracted = json.loads(json_str)
                return extracted
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                extracted = json.loads(json_str)
                return extracted
            else:
                raise
                
    except Exception as e:
        print(f"Error extracting scope change: {e}")
        return {
            "type": "ambiguous",
            "confidence": 0.0,
            "affects_deliverable": None,
            "detail": f"Error during extraction: {str(e)}",
            "explicitly_excluded": False,
            "new_deliverable": False,
            "effort_delta_hours": None,
            "dollar_impact": None,
            "risk_level": "high",
            "recommended_action": "flag_for_pm",
            "reasoning": "LLM extraction failed"
        }

# Made with Bob
