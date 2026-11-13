from dataclasses import dataclass, field


@dataclass(frozen=True)
class FoodProduct:
    barcode: str
    name: str
    brand: str
    quantity: str
    ingredients: str
    allergens: tuple = () # ("shrimp", "peanut")
    nutrition_per_100g: dict = field(default_factory=dict)
