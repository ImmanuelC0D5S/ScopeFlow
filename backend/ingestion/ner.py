"""Named Entity Recognition for contract documents."""
import re
from datetime import datetime
from typing import Any


def extract_entities(text: str) -> dict[str, Any]:
    """
    Extract named entities from contract text.
    
    Extracts:
    - Parties (company names)
    - Dates
    - Dollar amounts
    - Scope terms (deliverables, milestones)
    
    Args:
        text: Contract text
        
    Returns:
        Dictionary with extracted entities
    """
    entities = {
        "parties": extract_parties(text),
        "dates": extract_dates(text),
        "amounts": extract_dollar_amounts(text),
        "scope_terms": extract_scope_terms(text),
    }
    
    return entities


def extract_parties(text: str) -> list[str]:
    """
    Extract party names from contract text.
    
    Looks for patterns like:
    - "between X and Y"
    - "Party A: X"
    - Company names (capitalized multi-word phrases)
    """
    parties = []
    
    # Pattern: "between X and Y"
    between_pattern = r'between\s+([A-Z][A-Za-z\s&,\.]+?)\s+(?:and|&)\s+([A-Z][A-Za-z\s&,\.]+?)(?:\s|,|\.|;)'
    matches = re.finditer(between_pattern, text, re.IGNORECASE)
    for match in matches:
        party1 = match.group(1).strip()
        party2 = match.group(2).strip()
        if len(party1) > 2 and len(party1) < 100:
            parties.append(party1)
        if len(party2) > 2 and len(party2) < 100:
            parties.append(party2)
    
    # Pattern: "Party A:" or "Client:"
    party_label_pattern = r'(?:Party|Client|Vendor|Contractor|Company)\s*[A-Z]?\s*:\s*([A-Z][A-Za-z\s&,\.]+?)(?:\n|,|\.|;)'
    matches = re.finditer(party_label_pattern, text)
    for match in matches:
        party = match.group(1).strip()
        if len(party) > 2 and len(party) < 100:
            parties.append(party)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_parties = []
    for party in parties:
        party_clean = party.strip().rstrip(',.')
        if party_clean not in seen and party_clean:
            seen.add(party_clean)
            unique_parties.append(party_clean)
    
    return unique_parties[:10]  # Limit to 10 parties


def extract_dates(text: str) -> list[str]:
    """
    Extract dates from contract text.
    
    Recognizes formats:
    - MM/DD/YYYY
    - Month DD, YYYY
    - DD Month YYYY
    """
    dates = []
    
    # Pattern: MM/DD/YYYY or DD/MM/YYYY
    slash_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
    dates.extend(re.findall(slash_pattern, text))
    
    # Pattern: Month DD, YYYY (e.g., "January 15, 2024")
    month_pattern = r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b'
    dates.extend(re.findall(month_pattern, text, re.IGNORECASE))
    
    # Pattern: DD Month YYYY (e.g., "15 January 2024")
    day_month_pattern = r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b'
    dates.extend(re.findall(day_month_pattern, text, re.IGNORECASE))
    
    # Remove duplicates
    return list(set(dates))[:20]  # Limit to 20 dates


def extract_dollar_amounts(text: str) -> list[dict[str, Any]]:
    """
    Extract dollar amounts from contract text.
    
    Returns list of dicts with 'amount' and 'context'
    """
    amounts = []
    
    # Pattern: $X,XXX.XX or $X,XXX or $X
    dollar_pattern = r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    
    for match in re.finditer(dollar_pattern, text):
        amount_str = match.group(1).replace(',', '')
        try:
            amount = float(amount_str)
            # Get context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            amounts.append({
                "amount": amount,
                "formatted": f"${amount:,.2f}",
                "context": context
            })
        except ValueError:
            continue
    
    # Sort by amount descending
    amounts.sort(key=lambda x: x["amount"], reverse=True)
    
    return amounts[:10]  # Limit to top 10 amounts


def extract_scope_terms(text: str) -> list[str]:
    """
    Extract scope-related terms (deliverables, milestones, etc.).
    
    Looks for keywords like:
    - deliverable, milestone, phase
    - shall provide, will deliver
    - scope of work, services
    """
    scope_terms = []
    
    # Keywords that indicate scope items
    scope_keywords = [
        r'deliverable[s]?',
        r'milestone[s]?',
        r'phase[s]?',
        r'task[s]?',
        r'service[s]?',
        r'work product[s]?',
        r'output[s]?',
        r'requirement[s]?',
    ]
    
    # Find sentences containing scope keywords
    sentences = re.split(r'[.!?]\s+', text)
    
    for sentence in sentences:
        for keyword_pattern in scope_keywords:
            if re.search(keyword_pattern, sentence, re.IGNORECASE):
                # Clean and add sentence
                clean_sentence = sentence.strip()
                if 20 < len(clean_sentence) < 300:
                    scope_terms.append(clean_sentence)
                break  # Only add once per sentence
    
    return scope_terms[:15]  # Limit to 15 scope terms

# Made with Bob
