import re
import difflib
from typing import List, Dict, Optional
from sqlmodel import Session, select
from app.models import MasterPrice
from app.core.database import engine

class MedicineNER:
    def __init__(self):
        self._cached_medicines = None

    def _get_medicines(self, session: Session) -> List[Dict[str, str]]:
        if self._cached_medicines is None:
            statement = select(MasterPrice)
            results = session.exec(statement).all()
            self._cached_medicines = [
                {"code": p.procedure_code, "name": p.procedure_name, "normalized": self._normalize(p.procedure_name)}
                for p in results
            ]
        return self._cached_medicines

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Separate digits from letters (e.g., 50mg -> 50 mg)
        text = re.sub(r'(\d+)([a-z]+)', r'\1 \2', text)
        text = re.sub(r'([a-z]+)(\d+)', r'\1 \2', text)
        # Remove special chars except spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def find_matches(self, text: str, threshold: float = 0.8) -> List[Dict]:
        """
        Identifies potential medicine matches with improved filtering for units and common words.
        """
        normalized_query = self._normalize(text)
        if not normalized_query:
            return []

        # Common medical units and dosage forms that shouldn't drive matching
        STOP_WORDS = {'mg', 'tab', 'tablet', 'capsule', 'cap', 'syp', 'liquid', 'solution', 'ml', 'gm', 'mcg', 's', 't'}
        
        with Session(engine) as session:
            medicines = self._get_medicines(session)
        
        matches = []
        query_tokens = [t for t in normalized_query.split() if t not in STOP_WORDS]
        query_set = set(query_tokens)
        
        # Meaningful tokens are those that are NOT purely numeric
        meaningful_query_tokens = {t for t in query_tokens if not t.isdigit()}

        for med in medicines:
            med_normalized = med["normalized"]
            med_tokens = [t for t in med_normalized.split() if t not in STOP_WORDS]
            med_set = set(med_tokens)
            meaningful_med_tokens = {t for t in med_tokens if not t.isdigit()}

            # 1. Check for substring match
            # "dolo 650" should match "dolo 650 mg tablet"
            if normalized_query in med_normalized or med_normalized in normalized_query:
                score = difflib.SequenceMatcher(None, normalized_query, med_normalized).ratio()
                matches.append({
                    "code": med["code"],
                    "name": med["name"],
                    "score": max(0.9, score),  # High score for substring matches
                    "match_type": "substring"
                })
            
            # 2. Token overlap check - require meaningful token match
            else:
                overlap = query_set.intersection(med_set)
                meaningful_overlap = meaningful_query_tokens.intersection(meaningful_med_tokens)
                
                # We REQUIRE at least one "meaningful" (non-digit, non-unit) token to match
                if meaningful_overlap:
                    # Score based on how many tokens matched
                    score = len(overlap) / max(len(query_set), len(med_set))
                    
                    # Lower threshold to 0.3 to catch more matches
                    if score >= 0.3:
                        matches.append({
                            "code": med["code"],
                            "name": med["name"],
                            "score": score,
                            "match_type": "token_overlap"
                        })

        # Sort matches by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

    def map_item(self, item_name: str) -> Optional[Dict]:
        """
        Syntactic sugar for finding the single best match for an extracted item name.
        """
        matches = self.find_matches(item_name)
        if matches and matches[0]["score"] > 0.6:
            return matches[0]
        return None

medicine_ner = MedicineNER()
