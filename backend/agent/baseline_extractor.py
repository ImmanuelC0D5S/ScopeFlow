"""Scope baseline extraction using LLM."""
import json
from typing import Optional
import google.generativeai as genai
from backend.core.config import settings


BASELINE_EXTRACTION_PROMPT = """You are a contract analyst for a professional services firm.
Your job is to extract the scope baseline from a contract document.

Extract the following information and return it as valid JSON:

{
  "deliverables": [
    {
      "code": "D1",
      "description": "Brief description of deliverable",
      "estimated_hours": 40.0,
      "due_date": "2026-07-15"
    }
  ],
  "milestones": [
    {
      "name": "Phase 1 Complete",
      "date": "2026-06-30",
      "deliverables": ["D1", "D2"]
    }
  ],
  "exclusions": [
    "Mobile app development",
    "Third-party API integrations"
  ],
  "total_contract_value": 28000.00,
  "currency": "USD",
  "start_date": "2026-05-01",
  "end_date": "2026-08-31"
}

RULES:
- Assign sequential codes to deliverables (D1, D2, D3, etc.)
- Extract estimated hours if mentioned, otherwise set to null
- Extract due dates if mentioned, otherwise set to null
- List all explicitly excluded items
- Extract total contract value and currency
- If dates are not found, set to null
- Return ONLY the JSON object, no explanation

CONTRACT TEXT:
{contract_text}
"""


def extract_baseline_from_contract(
    contract_text: str,
    gemini_api_key: Optional[str] = None
) -> dict:
    """
    Extract scope baseline from contract text using Gemini.
    
    Args:
        contract_text: Full contract text
        gemini_api_key: Optional API key (uses settings if not provided)
        
    Returns:
        Dictionary with extracted baseline data
    """
    api_key = gemini_api_key or getattr(settings, 'gemini_api_key', None)
    
    if not api_key:
        # Return a placeholder baseline if no API key
        return {
            "deliverables": [],
            "milestones": [],
            "exclusions": [],
            "total_contract_value": 0.0,
            "currency": "USD",
            "start_date": None,
            "end_date": None
        }
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-002')
        
        # Truncate contract text if too long
        max_chars = 400000
        if len(contract_text) > max_chars:
            contract_text = contract_text[:max_chars] + "\n\n[... truncated ...]"
        
        prompt = BASELINE_EXTRACTION_PROMPT.format(contract_text=contract_text)
        
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0,
                'max_output_tokens': 4096,
            }
        )
        
        # Extract JSON from response
        response_text = response.text
        
        # Try to parse JSON
        try:
            baseline_data = json.loads(response_text)
            return baseline_data
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                baseline_data = json.loads(json_str)
                return baseline_data
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                baseline_data = json.loads(json_str)
                return baseline_data
            else:
                raise
                
    except Exception as e:
        print(f"Error extracting baseline: {e}")
        # Return empty baseline on error
        return {
            "deliverables": [],
            "milestones": [],
            "exclusions": [],
            "total_contract_value": 0.0,
            "currency": "USD",
            "start_date": None,
            "end_date": None,
            "error": str(e)
        }


def validate_baseline(baseline_data: dict) -> bool:
    """
    Validate that baseline data has required fields.
    
    Args:
        baseline_data: Dictionary with baseline data
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["deliverables", "exclusions", "total_contract_value"]
    
    for field in required_fields:
        if field not in baseline_data:
            return False
    
    # Validate deliverables structure
    if not isinstance(baseline_data["deliverables"], list):
        return False
    
    for deliverable in baseline_data["deliverables"]:
        if not isinstance(deliverable, dict):
            return False
        if "code" not in deliverable or "description" not in deliverable:
            return False
    
    return True

# Made with Bob
