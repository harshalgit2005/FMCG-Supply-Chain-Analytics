# ---------------------------------------------------------
# FMCG DEMAND CONFIGURATION
# ---------------------------------------------------------

CATEGORY_DEMAND = {
    "Food & Beverages": 1.25,
    "Packaged Foods": 1.15,
    "Personal Care": 0.85,
    "Household Care": 0.75,
}


REGION_DEMAND = {
    "West": 1.15,
    "North": 1.05,
    "South": 1.10,
    "East": 0.90,
}


STORE_TYPE_DEMAND = {
    "Hypermarket": 1.80,
    "Supermarket": 1.40,
    "Modern Trade": 1.25,
    "General Trade": 0.90,
    "Convenience Store": 0.65,
}


# Monthly demand multipliers.
#
# These create seasonality that forecasting
# models can later learn.

MONTHLY_SEASONALITY = {
    1: 0.95,
    2: 0.90,
    3: 1.00,
    4: 1.05,
    5: 1.10,
    6: 1.00,
    7: 0.95,
    8: 1.00,
    9: 1.05,
    10: 1.25,
    11: 1.35,
    12: 1.20,
}


WEEKEND_MULTIPLIER = 1.20


# Promotional uplift.
PROMOTION_PROBABILITY = 0.08

PROMOTION_MULTIPLIER = 1.30


# Demand variability by product type.
DEMAND_NOISE = {
    "Food & Beverages": 0.15,
    "Packaged Foods": 0.18,
    "Personal Care": 0.12,
    "Household Care": 0.10,
}