"""
Country mapping between sheet codes and data values
"""

COUNTRY_MAPPING = {
    'FR🇫🇷': 'France',
    'ES🇪🇸': 'Spain',
    'UK🇬🇧': 'United Kingdom',
    'PT🇵🇹': 'Portugal',
    'NL🇳🇱': 'Netherlands',
    'DE🇩🇪': 'Germany',
    'IT🇮🇹': 'Italy',
    'BEL🇧🇪': 'Belgium'
}

def get_country_data_value(country_code: str) -> str:
    """
    Convert country code from sheet name to data value.
    
    Args:
        country_code: Code like 'FR🇫🇷'
        
    Returns:
        Data value like 'France'
    """
    return COUNTRY_MAPPING.get(country_code, country_code)

def get_country_code(data_value: str) -> str:
    """
    Convert data value to country code.
    
    Args:
        data_value: Value like 'France'
        
    Returns:
        Code like 'FR🇫🇷'
    """
    for code, value in COUNTRY_MAPPING.items():
        if value == data_value:
            return code
    return data_value
