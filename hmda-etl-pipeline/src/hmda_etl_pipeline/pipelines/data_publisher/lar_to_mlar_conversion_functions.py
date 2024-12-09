import math


def convert_age(age: int) -> str:
    """Converts a given age from an exact value to an age range.

    Args:
        age (int): The exact age.

    Returns:
        str: The age range that contains the exact age.
    """
    if age == 8888:
        return "8888"
    elif age == 9999:
        return "9999"
    elif age < 25:
        return "<25"
    elif age < 35:
        return "25-34"
    elif age < 45:
        return "35-44"
    elif age < 55:
        return "45-54"
    elif age < 65:
        return "55-64"
    elif age < 75:
        return "65-74"
    elif age > 74:
        return ">74"


def is_age_greater_than_62(age: int) -> str:
    """Evaluates if a given age is greater than or equal to 62.

    Args:
        age (int): The age to be compared to 62.

    Returns:
        str: "Yes" if an age is greater than or equal to 62,
            otherwise "No". Returns "NA" if age is 8888 or 9999.
    """
    if age == 8888 or age == 9999:
        return "NA"
    elif age >= 62:
        return "Yes"
    elif age < 62:
        return "No"


def convert_debt_to_income_ratio(ratio: str) -> str:
    """Converts the exact ratio of debt to income into a range of
    percentages. Returns the input ratio if it "NA", "Exempt", or empty.

    Args:
        ratio (str): The exact ratio of debt to income.

    Returns:
        str: A range of percentages that contains the exact ratio.
    """
    if ratio == "NA" or ratio == "Exempt" or ratio == "":
        return ratio
    ratio_int = int(float(ratio))
    if ratio_int < 20:
        return "<20%"
    elif ratio_int < 30:
        return "20%-<30%"
    elif ratio_int < 36:
        return "30%-<36%"
    elif ratio_int < 50:
        return str(ratio_int)
    elif ratio_int < 61:
        return "50%-60%"
    elif ratio_int > 60:
        return ">60%"


def income_categorization(lar_income: str, census_median_income: int) -> str:
    """Convert income into a percent range of the median msa income. Returns
    "NA" if the income is "NA" or empty.

    Args:
        lar_income (str): The exact income.
        census_median_income (int): The median income.

    Returns:
        str: A range of percentages that contains the exact income compared
        to the median income.
    """
    if lar_income == "NA" or lar_income == "":
        return "NA"

    # Income in the lar is rounded to 1000
    income = float(lar_income) * 1000
    fifty = census_median_income * 0.5
    eighty = census_median_income * 0.8
    one_twenty = census_median_income * 1.2
    if income < fifty:
        return "<50%"
    elif (income >= fifty) & (income < eighty):
        return "50-79%"
    elif (income >= eighty) & (income < census_median_income):
        return "80-99%"
    elif (income >= census_median_income) & (income < one_twenty):
        return "100-119%"
    else:
        return ">120%"


def convert_total_units(total_units: int) -> str:
    """Converts the exact number of total units into a range. If the
    total is less than 5, the exact number is returned.

    Args:
        total_units (int): The exact number of total units.

    Returns:
        str: A range of numbers that contains the exact number of total
            units.
    """
    if total_units < 5:
        return str(total_units)
    elif total_units < 25:
        return "5-24"
    elif total_units < 50:
        return "25-49"
    elif total_units < 100:
        return "50-99"
    elif total_units < 150:
        return "100-149"
    elif total_units > 149:
        return ">149"


def convert_multifamily_affordable_units(
    multifamily_units: str, total_units: int
) -> str:
    """Calculates the percentage of units that are multifamily
    affordable units.

    Args:
        multifamily_units (str): The exact number of multifamily
            affordable units.
        total_units (int): The exact number of total units.

    Returns:
        str: The percentage of units that are multifamily affordable
            units. Or one of "NA", "Exempt", or "".
    """
    if multifamily_units in ["NA", "Exempt", ""]:
        return multifamily_units

    percentage = (float(multifamily_units) / float(total_units)) * 100
    return str(round(percentage))


def convert_property_value(property_value: str) -> str:
    """Converts the property value from the exact value to a rounded
    value.

    Args:
        property_value (str): The exact property value.

    Returns:
        str: A rounded property value.
    """
    if property_value == "NA" or property_value == "Exempt" or property_value == "":
        return property_value
    return round_to_midpoint(int(float(property_value)))


def round_to_midpoint(x: float) -> str:
    """Returns the rounded midpoint as a string of a given number.

    Args:
        x (float): Float number to round.

    Returns:
        str: Rounded int result as a string.
    """
    rounded = 10000 * math.floor((x / 10000)) + 5000
    return str(int(rounded))


def median_age_calculated(
    filing_year: int, tract_median_age_of_housing_units: int
) -> str:
    """Returns the year range when given the filing year and the median
    age of housing units in a tract.

    Args:
        filing_year (int): The current filing year.
        tract_median_age_of_housing_units (int): The median age of housing
            units in a tract.

    Returns:
        str: A range of years.
    """
    
    median_year = filing_year - tract_median_age_of_housing_units
    if tract_median_age_of_housing_units == -1:
        return "Age Unknown"
    elif median_year <= 1969:
        return "1969 or Earlier"
    elif (median_year >= 1970) & (median_year <= 1979):
        return "1970 - 1979"
    elif (median_year >= 1980) & (median_year <= 1989):
        return "1980 - 1989"
    elif (median_year >= 1990) & (median_year <= 1999):
        return "1990 - 1999"
    elif (median_year >= 2000) & (median_year <= 2010):
        return "2000 - 2010"
    elif median_year >= 2011:
        return "2011 - Present"
    else:
        return "Age Unknown"
