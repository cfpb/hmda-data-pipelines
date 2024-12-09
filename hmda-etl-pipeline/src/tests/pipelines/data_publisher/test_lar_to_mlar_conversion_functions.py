"""
Verify the LAR to MLAR conversion helper functions work as expected.
"""

from hmda_etl_pipeline.pipelines.data_publisher.lar_to_mlar_conversion_functions import (
    convert_age,
    convert_debt_to_income_ratio,
    convert_multifamily_affordable_units,
    convert_property_value,
    convert_total_units,
    income_categorization,
    is_age_greater_than_62,
    median_age_calculated,
    round_to_midpoint,
)


def test_convert_age():
    """Verify that the helper function convert_age correctly converts a
    given age from an exact value to an age range.
    """

    # Verify that 8888 and 9999 inputs are returned as a string
    assert convert_age(8888) == "8888"
    assert convert_age(9999) == "9999"

    # Verify that normal ages have the correct range returned
    assert convert_age(24) == "<25"

    assert convert_age(25) == "25-34"
    assert convert_age(34) == "25-34"

    assert convert_age(35) == "35-44"
    assert convert_age(44) == "35-44"

    assert convert_age(45) == "45-54"
    assert convert_age(54) == "45-54"

    assert convert_age(55) == "55-64"
    assert convert_age(64) == "55-64"

    assert convert_age(65) == "65-74"
    assert convert_age(74) == "65-74"

    assert convert_age(75) == ">74"


def test_is_age_greater_than_62():
    """Verify that the helper function is_age_greater_than_62 correctly
    evaluates if a given age is greater than or equal to 62.
    """

    # Verify that 8888 and 9999 inputs return NA
    assert is_age_greater_than_62(8888) == "NA"
    assert is_age_greater_than_62(9999) == "NA"

    # Verify that other ages return the correct result
    assert is_age_greater_than_62(61) == "No"
    assert is_age_greater_than_62(62) == "Yes"
    assert is_age_greater_than_62(63) == "Yes"


def test_convert_debt_to_income_ratio():
    """Verify that the helper function convert_debt_to_income_ratio
    correctly converts the exact ratio of debt to income into a range of
    percentages.
    """

    # Verify that NA inputs are returned as a string
    assert convert_debt_to_income_ratio("NA") == "NA"
    assert convert_debt_to_income_ratio("Exempt") == "Exempt"
    assert convert_debt_to_income_ratio("") == ""

    # Verify that normal ratios have the correct range returned
    assert convert_debt_to_income_ratio("19.9") == "<20%"

    assert convert_debt_to_income_ratio("20") == "20%-<30%"
    assert convert_debt_to_income_ratio("29.9") == "20%-<30%"

    assert convert_debt_to_income_ratio("30") == "30%-<36%"
    assert convert_debt_to_income_ratio("35.9") == "30%-<36%"

    assert convert_debt_to_income_ratio("36") == "36"
    assert convert_debt_to_income_ratio("49.9") == "49"

    assert convert_debt_to_income_ratio("50") == "50%-60%"
    assert convert_debt_to_income_ratio("60.9") == "50%-60%"

    assert convert_debt_to_income_ratio("61") == ">60%"

def test_income_categorization():
    """Verify that the helper function income_categorization correctly
    converts the exact income into a percent range of the median msa income
    or returns "NA" if the income is "NA" or empty.
    """
    
    # Verify that NA inputs are returned as a string
    assert income_categorization("NA", 100000) == "NA"
    assert income_categorization("", 100000) == "NA"
    
    # Verify that normal incomes have the correct percentage range  returned
    assert income_categorization("49", 100000) == "<50%"
    
    assert income_categorization("50", 100000) == "50-79%"
    assert income_categorization("79", 100000) == "50-79%"
    
    assert income_categorization("80", 100000) == "80-99%"
    assert income_categorization("99", 100000) == "80-99%"
    
    assert income_categorization("100", 100000) == "100-119%"
    assert income_categorization("119", 100000) == "100-119%"
    
    assert income_categorization("120", 100000) == ">120%"


def test_convert_total_units():
    """Verify that the helper function convert_total_units correctly
    converts the exact number of total units into a range. If the total
    is less than 5, the exact number is returned.
    """

    assert convert_total_units(4) == "4"

    assert convert_total_units(5) == "5-24"
    assert convert_total_units(24) == "5-24"

    assert convert_total_units(25) == "25-49"
    assert convert_total_units(49) == "25-49"

    assert convert_total_units(50) == "50-99"
    assert convert_total_units(99) == "50-99"

    assert convert_total_units(100) == "100-149"
    assert convert_total_units(149) == "100-149"

    assert convert_total_units(150) == ">149"


def test_convert_multifamily_affordable_units():
    """Verify that the helper function
    convert_multifamily_affordable_units correctly calculates the
    percentage of units that are multifamily affordable units.
    """

    # Verify that NA inputs are returned as a string
    assert convert_multifamily_affordable_units("NA", 5) == "NA"
    assert convert_multifamily_affordable_units("Exempt", 5) == "Exempt"
    assert convert_multifamily_affordable_units("", 5) == ""

    # Test various percentages
    assert convert_multifamily_affordable_units("2", 8) == "25"
    assert convert_multifamily_affordable_units("1", 3) == "33"
    assert convert_multifamily_affordable_units("1", 2) == "50"
    assert convert_multifamily_affordable_units("1", 1) == "100"


def test_convert_property_value():
    """Verify that the helper function convert_property_value correctly
    converts the property value from the exact value to a rounded value.
    """

    # Verify that NA inputs are returned as a string
    assert convert_property_value("NA") == "NA"
    assert convert_property_value("Exempt") == "Exempt"
    assert convert_property_value("") == ""

    # Test various property values
    assert convert_property_value("100.9") == "5000"
    assert convert_property_value("10000") == "15000"
    assert convert_property_value("101000") == "105000"
    assert convert_property_value("210000") == "215000"


def test_round_to_midpoint():
    """Verify that the helper function round_to_midpoint correctly
    returns the rounded midpoint as a string of a given number.
    """

    # Test various property values
    assert round_to_midpoint(100.9) == "5000"
    assert round_to_midpoint(10000) == "15000"
    assert round_to_midpoint(101000) == "105000"
    assert round_to_midpoint(210000) == "215000"
    
    
def test_median_age_calculated():
    """Verify that the helper function median_age_calculated correctly
    returns the year range when given the filing year and the median
    age of housing units in a tract.
    """
    
    # Verify that "Age Unknown" is returned if tract_median_age_of_housing_units is -1
    assert median_age_calculated(2023, -1) == "Age Unknown"

    # Test various property values
    assert median_age_calculated(2023, 54) == "1969 or Earlier"

    assert median_age_calculated(2023, 53) == "1970 - 1979"
    assert median_age_calculated(2023, 44) == "1970 - 1979"

    assert median_age_calculated(2023, 43) == "1980 - 1989"
    assert median_age_calculated(2023, 34) == "1980 - 1989"

    assert median_age_calculated(2023, 33) == "1990 - 1999"
    assert median_age_calculated(2023, 24) == "1990 - 1999"

    assert median_age_calculated(2023, 23) == "2000 - 2010"
    assert median_age_calculated(2023, 13) == "2000 - 2010"

    assert median_age_calculated(2023, 12) == "2011 - Present"
