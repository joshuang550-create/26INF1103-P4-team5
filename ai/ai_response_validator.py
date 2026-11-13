import json
import math

from prompts.ai_prompts import EXPECTED_KEYS, NUTRIENT_KEYS
from ai.validation_result import ValidationResult
from ai.assessment import Assessment


class AIResponseValidator:
    def __init__(self):
        self._checks = [ # if new checks are needed, just create the private staticmethod and add it here
            self._check_keys, 
            self._check_information_needed, 
            self._check_portion, 
            self._check_nutrient, 
            self._check_reason, 
            self._check_potential_concern, 
            self._check_confidence_score
        ]

    # =========== Helper Methods ===========
    @staticmethod
    def _parse(response_text):
        try:
            data = json.loads(response_text) if isinstance(response_text, str) else response_text # if string, json.loads to a dict, else keep it as is
        except json.JSONDecodeError:
            return None, "invalid_json"

        if not isinstance(data, dict):
            return None, "invalid_structure" # if not a dict

        return data, None # valid data

    # =========== Public Method ===========
    def validate(self, response_text):
        data, issue = self._parse(response_text)

        if issue:
            return ValidationResult(issues=(issue,)) # if response_text cannot be parsed properly, not a dict
        
        issues = [i for check in self._checks for i in check(data)] # response_text is a dict, then run every check in self.checks 

        if issues:
            return ValidationResult(issues=tuple(issues)) # if there is even 1 issue, return issues without assessment

        return ValidationResult(assessment=Assessment(**data)) # if there is no issues at all, return assessment without issues

    def validate_recommendations(self, response_text): # the fallback reply should be a list of dicts {"recommendations": [{"food": "...", "reason": "..."}]}
        data, issue = self._parse(response_text)
        if issue or set(data) != {"recommendations"}:
            return None

        items = data["recommendations"]
        if not isinstance(items, list) or not 1 <= len(items) <= 10:
            return None

        recommendations = []
        for item in items:
            if not isinstance(item, dict) or set(item) != {"food", "reason"}:
                return None
            if not all(isinstance(item[key], str) and item[key].strip() for key in ("food", "reason")):
                return None
            recommendations.append({"food": item["food"].strip(), "reason": item["reason"].strip()})
        return recommendations
    
    # =========== Private Methods ===========
    @staticmethod
    def _check_keys(data):
        if set(data) != EXPECTED_KEYS:
            return ["invalid_keys"]
        return []

    @staticmethod
    def _check_information_needed(data):
        questions = data.get("information_needed")

        if isinstance(questions, list) and all(isinstance(q, str) and q.strip() for q in questions):
            return []
        
        return ["invalid_information_needed"]

    @staticmethod
    def _check_portion(data):
        portion, questions = data.get("portion_g"), data.get("information_needed")

        if not (isinstance(portion, (int, float)) and not isinstance(portion, bool) and math.isfinite(portion)) or portion < 0: 
            return ["invalid_portion"]
        
        if questions == [] and portion == 0: # assessed, but no portion given
            return ["invalid_portion"]
        
        return []

    @staticmethod
    def _check_nutrient(data):
        nutrients = data.get("nutrients")

        if not isinstance(nutrients, dict) or set(nutrients) != set(NUTRIENT_KEYS):
            return ["invalid_nutrient"]
        
        if not all((isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)) and v >= 0 for v in nutrients.values()):
            return ["invalid_nutrient"]
        
        return []

    @staticmethod
    def _check_reason(data):
        reason = data.get("reason")
        if isinstance(reason, str) and reason.strip():
            return []
        return ["invalid_reason"]

    @staticmethod
    def _check_potential_concern(data):
        potential_concern = data.get("potential_concern")
        if isinstance(potential_concern, bool):
            return []
        return ["invalid_potential_concern"]

    @staticmethod
    def _check_confidence_score(data):
        score = data.get("confidence_score")
        if type(score) is int and 0 <= score <= 100:
            return []
        return ["invalid_confidence_score"]
