import re


class AllergenDetector:
    def __init__(self, synonyms):
        self._synonyms = synonyms # from DataManager.get_allergens()

    # =========== Private Helper ===========
    def _get_synonyms(self, allergies): # takes allergies and matches against synonyms to return only the category and matched word. This means it only allergens the user is allergic to will be flagged.
        found = {}
        for category, words in self._synonyms.items():
            for word in words:
                for allergy in allergies: # allergies is a list ["shrimp allergy", "peanut allergy"]
                    if re.search(rf"\b{re.escape(word)}s?\b", allergy, re.IGNORECASE):
                        found.setdefault(category, []).append(word)
        return found # example return {"shellfish_mollusk": ["clam"]}

    # =========== Public Method ===========
    def detect(self, text, allergies): # allergies is a list ["shrimp allergy", "peanut allergy"]
        found = {}
        for category, words in self._get_synonyms(allergies).items(): # {category: [word, word, word], category: [word, word, word]}
            for word in words:
                if re.search(rf"\b{re.escape(word)}s?\b", text, re.IGNORECASE):
                    found.setdefault(category, []).append(word) # if category exists in found, add to it, else create it
        return found
