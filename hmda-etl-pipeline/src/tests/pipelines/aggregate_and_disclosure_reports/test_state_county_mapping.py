import pandas as pd

from hmda_etl_pipeline.pipelines.aggregate_and_disclosure_reports.state_county_mapping import create_state_and_county_tract

def test_create_state_and_county_tract():
    """Verify that the helper function create_state_and_county_tract
    correctly gets the state, county, and remaining tract names when given
    a tract name and the state_county_mapping_df.
    """
    
    # Create state_county_mapping_df
    data = {"county_name": ["A County Name", "B County Name"],
        "state_name": ["WA", "CA"],
        "state_code": [12, 67],
        "county_code": [345, 890]}
    state_county_mapping_df = pd.DataFrame(data)
    
    # Verify that NA/NA/NA is returned if either the state or county code
    # is not found in state_county_mapping_df
    result_no_state_or_county = create_state_and_county_tract("99999123456", state_county_mapping_df)
    assert(result_no_state_or_county == "NA/NA/NA")
    result_no_state = create_state_and_county_tract("12999000000", state_county_mapping_df)
    assert(result_no_state == "NA/NA/NA")
    result_no_county = create_state_and_county_tract("99345000000", state_county_mapping_df)
    assert(result_no_county == "NA/NA/NA")
    
    # Verify NA is returned if the tract length is not 11 or NA
    result_no_state_or_county = create_state_and_county_tract("NA", state_county_mapping_df)
    assert(result_no_state_or_county == "NA/NA/NA")
    result_no_state_or_county = create_state_and_county_tract("12345", state_county_mapping_df)
    assert(result_no_state_or_county == "NA/NA/NA")
    
    # Verify the correct string is returned if the state and county codes exist
    result_valid_a = create_state_and_county_tract("12345000000", state_county_mapping_df)
    assert(result_valid_a == "A County Name/WA/000000")
    result_valid_b = create_state_and_county_tract("67890123456", state_county_mapping_df)
    assert(result_valid_b == "B County Name/CA/123456")