from typing import Tuple

def format_quantity(value: float, unit: str) -> Tuple[float, str, str]:
    """
    Formats a decimal into a human-readable string with fractions and unit swaps.
    Returns (updated_value, updated_unit, display_string)
    """
    # 1. Unit Swaps (Downgrading)
    if unit.lower() in ['cup', 'cups'] and value < 0.25:
        value *= 16
        unit = 'tbsp'
        
    if unit.lower() in ['tbsp', 'tablespoon', 'tablespoons'] and value < 1.0:
        value *= 3
        unit = 'tsp'
        
    if unit.lower() in ['lb', 'lbs', 'pound', 'pounds'] and value < 1.0:
        value *= 16
        unit = 'oz'

    # 2. Decimal to Fraction Rounding
    integer_part = int(value)
    decimal_part = value - integer_part
    
    fraction_str = ""
    if 0.18 <= decimal_part < 0.29:
        fraction_str = "1/4"
        decimal_val = 0.25
    elif 0.29 <= decimal_part < 0.37:
        fraction_str = "1/3"
        decimal_val = 0.333
    elif 0.38 <= decimal_part < 0.58:
        fraction_str = "1/2"
        decimal_val = 0.5
    elif 0.59 <= decimal_part < 0.70:
        fraction_str = "2/3"
        decimal_val = 0.666
    elif 0.71 <= decimal_part < 0.85:
        fraction_str = "3/4"
        decimal_val = 0.75
    elif decimal_part >= 0.86:
        integer_part += 1
        fraction_str = ""
        decimal_val = 0.0
    else:
        decimal_val = decimal_part # Keep as is if below 0.18

    # Construct final display string
    if integer_part > 0 and fraction_str:
        display_str = f"{integer_part} {fraction_str}"
    elif integer_part > 0:
        display_str = str(integer_part)
    elif fraction_str:
        display_str = fraction_str
    else:
        if value == 0:
            display_str = "0"
        else:
            display_str = f"{value:g}"

    return float(integer_part + decimal_val), unit, display_str
