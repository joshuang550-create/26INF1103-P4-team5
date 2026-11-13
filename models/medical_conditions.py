from exceptions.invalid_input_error import InvalidInputError


class MedicalConditions:
    def __init__(self, conditions=None):
        self._conditions = list(conditions or []) # fresh copy everytime

    # =========== Attribute Validation ===========
    @staticmethod
    def validate_condition(value): # format validator, datamanager has the csv check validator
        if len(value.strip().lower()) <= 1:
            raise InvalidInputError("Please try to enter a recognised name for your medical condition.")
        return value.strip().lower()

    # =========== Edit ===========
    def add_conditions(self, conditions): # takes in a list instead of 1 by 1. For compatibility with GUI.
        validated_conditions = [self.validate_condition(condition) for condition in conditions]
        self._conditions.extend(validated_conditions)

    def remove_conditions(self, condition_indices): # used to be 1 by 1, now it takes in a list of integers. Idea is that the GUI will allow the user to tick the conditions to remove, stored as a list of integers.
        to_remove = set(condition_indices)
        self._conditions = [c for i, c in enumerate(self._conditions) if i not in to_remove]

    # =========== Utility =========== 
    def matches_any(self, keywords): # returns True if any keywords are found in list of medical conditions
        return any(keyword.lower() in condition.lower() for condition in self._conditions for keyword in keywords) # no need for regex since rapidfuzz will ensure only valid medical conditions are in the list

    def to_list(self):
        return list(self._conditions) # "read-only" since it is a copy, will not affect original

    def __len__(self):
        return len(self._conditions)
