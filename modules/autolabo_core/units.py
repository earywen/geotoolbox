"""
Smart Unit Conversion for AutoLabo.

Handles automatic unit conversion between different metric prefixes
commonly used in laboratory reports (ng, µg, mg, g per L or kg).
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Unit prefix multipliers (base unit = 1)
# All values expressed relative to base unit (g for mass, L for volume)
PREFIX_MULTIPLIERS = {
    'p': 1e-12,   # pico
    'n': 1e-9,    # nano
    'µ': 1e-6,    # micro
    'u': 1e-6,    # micro (ASCII fallback)
    'm': 1e-3,    # milli
    '': 1,        # base unit (g, L)
    'k': 1e3,     # kilo
}

# Common concentration unit patterns
# Format: (mass_prefix, volume_unit)
UNIT_PATTERN = re.compile(
    r'^(p|n|µ|u|m|k)?g[/\s]*(L|l|kg|Kg|KG)$',
    re.IGNORECASE
)


def parse_unit(unit_str: str) -> Optional[Tuple[float, str]]:
    """
    Parse a concentration unit string into multiplier and base.
    
    Args:
        unit_str: Unit string like "µg/L", "mg/kg", "ng/L"
        
    Returns:
        Tuple of (multiplier, base_unit) or None if parsing failed
        Example: "µg/L" -> (1e-6, "L"), "mg/kg" -> (1e-3, "kg")
    """
    if not unit_str or not isinstance(unit_str, str):
        return None
    
    # Normalize unit string
    unit_clean = unit_str.strip().replace(' ', '')
    
    # Try to match pattern
    match = UNIT_PATTERN.match(unit_clean)
    if not match:
        # Try common variations
        unit_clean = unit_clean.replace('ug/', 'µg/').replace('μg/', 'µg/')
        match = UNIT_PATTERN.match(unit_clean)
        if not match:
            return None
    
    prefix = match.group(1) or ''
    volume = match.group(2).upper()
    
    # Normalize volume unit
    if volume in ('L', 'l'):
        base = 'L'
    elif volume in ('KG', 'Kg', 'kg'):
        base = 'kg'
    else:
        base = volume
    
    multiplier = PREFIX_MULTIPLIERS.get(prefix.lower() if prefix else '', None)
    if multiplier is None:
        return None
    
    return (multiplier, base)


def get_conversion_factor(from_unit: str, to_unit: str) -> Optional[float]:
    """
    Calculate conversion factor between two units.
    
    Args:
        from_unit: Source unit (e.g., "mg/L")
        to_unit: Target unit (e.g., "µg/L")
        
    Returns:
        Conversion factor (multiply source value by this) or None if incompatible
    """
    from_parsed = parse_unit(from_unit)
    to_parsed = parse_unit(to_unit)
    
    if not from_parsed or not to_parsed:
        return None
    
    from_mult, from_base = from_parsed
    to_mult, to_base = to_parsed
    
    # Units must have same base (L or kg)
    if from_base != to_base:
        logger.warning(f"Incompatible unit bases: {from_base} vs {to_base}")
        return None
    
    # Calculate factor: from_value * factor = to_value
    factor = from_mult / to_mult
    return factor


def convert_value(value: float, from_unit: str, to_unit: str) -> Optional[float]:
    """
    Convert a value from one unit to another.
    
    Args:
        value: Numeric value to convert
        from_unit: Source unit
        to_unit: Target unit
        
    Returns:
        Converted value or None if conversion not possible
    """
    factor = get_conversion_factor(from_unit, to_unit)
    if factor is None:
        return None
    
    return value * factor


def units_are_compatible(unit1: str, unit2: str) -> bool:
    """
    Check if two units can be converted between each other.
    """
    parsed1 = parse_unit(unit1)
    parsed2 = parse_unit(unit2)
    
    if not parsed1 or not parsed2:
        return False
    
    return parsed1[1] == parsed2[1]  # Same base (L or kg)


def normalize_to_reference(raw_value: float, raw_unit: str, ref_unit: str) -> Tuple[Optional[float], bool]:
    """
    Normalize a raw lab value to match the reference unit.
    
    Args:
        raw_value: Value from lab file
        raw_unit: Unit from lab file
        ref_unit: Unit from reference file
        
    Returns:
        Tuple of (converted_value, was_converted)
        If conversion not needed or not possible, returns (raw_value, False)
    """
    # Quick check: are they the same?
    if raw_unit.strip().lower() == ref_unit.strip().lower():
        return (raw_value, False)
    
    # Try conversion
    factor = get_conversion_factor(raw_unit, ref_unit)
    if factor is None:
        logger.debug(f"Cannot convert {raw_unit} to {ref_unit}")
        return (raw_value, False)
    
    if factor == 1.0:
        return (raw_value, False)
    
    converted = raw_value * factor
    logger.info(f"⚡ Unit conversion: {raw_value} {raw_unit} → {converted} {ref_unit}")
    return (converted, True)
