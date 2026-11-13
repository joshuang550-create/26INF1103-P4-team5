class FoodLookupError(Exception):
    title = "Barcode Lookup Failed"
    description = "Could not look up that barcode right now. You can continue without barcode data, or try again."
