# Scope Change Detection Prompt

## System Prompt

```
You are a scope change analyst for a professional services firm.
Your job is to read client communications and determine whether they
contain a scope change, compared to the original agreed contract.

You must always return valid JSON. No explanation, no preamble.
```

---

## User Prompt Template

```
## Original Scope Baseline

DELIVERABLES:
{{deliverables}}

EXCLUSIONS:
{{exclusions}}

TOTAL CONTRACT VALUE: {{total_value}}

---

## New Client Communication

SOURCE: {{source}}        # e.g. email, Slack, meeting note
DATE: {{date}}
FROM: {{sender}}

MESSAGE:
{{message_body}}

---

## Instructions

Analyze the message against the original scope baseline and return JSON with the following fields:

{
  "type": "scope_change" | "clarification" | "admin" | "ambiguous",
  "confidence": 0.0 to 1.0,
  "affects_deliverable": "<deliverable id or null>",
  "detail": "<one sentence describing what changed>",
  "explicitly_excluded": true | false,
  "new_deliverable": true | false,
  "effort_delta_hours": <number or null if unknown>,
  "dollar_impact": <number or null if unknown>,
  "risk_level": "low" | "medium" | "high",
  "recommended_action": "auto_approve" | "flag_for_pm" | "ignore",
  "reasoning": "<one sentence explaining your verdict>"
}

RULES:
- If the message is just a question or status check, type = "clarification"
- If the message requests work that is in the exclusions list, set explicitly_excluded = true
- If confidence is below 0.75, always set recommended_action = "flag_for_pm"
- If dollar_impact is unknown but effort_delta_hours is known, leave dollar_impact null
- Never invent deliverable IDs that are not in the baseline
- Never return anything outside the JSON object
```

---

## Example: Filled Prompt

```
## Original Scope Baseline

DELIVERABLES:
- D1: Build user authentication module | 40 hrs | due 2026-07-15
- D2: Deploy to AWS staging environment | 16 hrs | due 2026-08-01

EXCLUSIONS:
- Mobile app development
- Third-party API integrations

TOTAL CONTRACT VALUE: $28,000

---

## New Client Communication

SOURCE: email
DATE: 2026-05-14
FROM: client@acmecorp.com

MESSAGE:
"Hey, can we also add a mobile app version of the auth module?
Would be great to have it ready alongside the web version."

---

## Instructions

[...same instructions as above...]
```

---

## Example: Expected Output

```json
{
  "type": "scope_change",
  "confidence": 0.94,
  "affects_deliverable": "D1",
  "detail": "Client requesting mobile app version of authentication module",
  "explicitly_excluded": true,
  "new_deliverable": false,
  "effort_delta_hours": null,
  "dollar_impact": null,
  "risk_level": "high",
  "recommended_action": "flag_for_pm",
  "reasoning": "Mobile app development is explicitly listed as an exclusion in the original contract."
}
```

---

## Risk Rule Engine (post-prompt logic)

Apply these rules **after** the LLM returns JSON — in your backend code, not in the prompt.

| Condition | Override action |
|---|---|
| `confidence < 0.75` | Always `flag_for_pm` |
| `dollar_impact > 5000` | Always `flag_for_pm` |
| `explicitly_excluded = true` | Always `flag_for_pm` |
| `new_deliverable = true` | Always `flag_for_pm` |
| `type = "clarification"` | Always `ignore` |
| `type = "admin"` | Always `ignore` |

---

## Notes

- Feed this prompt to `gemini-1.5-pro-002` or `gpt-4o`
- Set `temperature: 0` for deterministic extraction
- Validate the JSON response with Pydantic before passing downstream
- Log every LLM call with: input message, output JSON, timestamp, and model version
- Never use the LLM output directly to trigger actions — always run the risk rule engine first
