import pandas as pd

def create_state_and_county_tract(
    tract_name: str, state_county_mapping_df: pd.DataFrame
):
    """Returns tract string given state and county codes.

    Args:
        tract_name (str): An int where the first two digits are the
            state code, the next three digits are the county code, and the remaining
            six digits are the remaining tract number.
        state_county_mapping_df (pd.DataFrame): State and county code lookup map.
    Returns:
        A tract string in the form of county_name/state_name/remaining_tract_number
    """
    
    tract = "NA/NA/NA"

    # Check if the tract is the right length and not NA
    if len(tract_name) == 11:
        
        # Get state and county codes
        state_code = int(tract_name[:2])
        county_code = int(tract_name[2:5])

        # Find state and county names
        state_and_county = state_county_mapping_df[
            (state_county_mapping_df["state_code"] == state_code)
            & (state_county_mapping_df["county_code"] == county_code)
        ]
        
        # Create the tract if the state and county names are found
        if state_and_county.shape[0] > 0:
            state_name = state_and_county["state_name"].iloc[0]
            county_name = state_and_county["county_name"].iloc[0]
            remaining_tract = tract_name[5:]
            
            # Create tract
            tract = county_name + "/" + state_name + "/" + remaining_tract
    
    return tract