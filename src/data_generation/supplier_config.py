# ---------------------------------------------------------
# SUPPLIER PERFORMANCE CONFIGURATION
# ---------------------------------------------------------

SUPPLIER_PROFILES = {
    "Excellent": {
        "lead_time_min": 2,
        "lead_time_max": 4,
        "fill_rate": 0.98,
        "damage_rate": 0.005,
        "late_probability": 0.04,
    },

    "Good": {
        "lead_time_min": 3,
        "lead_time_max": 6,
        "fill_rate": 0.95,
        "damage_rate": 0.010,
        "late_probability": 0.08,
    },

    "Average": {
        "lead_time_min": 5,
        "lead_time_max": 9,
        "fill_rate": 0.91,
        "damage_rate": 0.020,
        "late_probability": 0.15,
    },

    "Poor": {
        "lead_time_min": 7,
        "lead_time_max": 14,
        "fill_rate": 0.85,
        "damage_rate": 0.035,
        "late_probability": 0.25,
    },
}