from dataclasses import dataclass


@dataclass(frozen=True)
class RiskContext: # this helps RiskRule later so that it only takes the context it needs (allergens_found is only needed for AllergenRule)
    profile: object
    assessment: object
    allergens_found: dict
