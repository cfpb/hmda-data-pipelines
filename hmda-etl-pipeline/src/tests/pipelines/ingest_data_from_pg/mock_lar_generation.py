"""This script creates two mock dataframes for testing the LAR 
partitioning logic. 

All data is artificially generated and no PII is contained within the 
mock data. LEIs are random strings and likely do not correspond to 
actual institutions. 

The first dataframe is called `mock_pg_lar_data` and contains the 
following columns: 

    [lei, row_number, action_taken_date, application_date]
    
The second dataframe is called `lar_row_counts_by_lei` and maps the 20
fake LEIs to how many times they appear in `mock_pg_lar_data`."""


import numpy as np
import pandas as pd

# these are 20 random strings of length 20 containing 0-9 and A-Z
# generated using this website: https://www.random.org/strings/
leis = [
    "SXVKXL8NUULLAYRNJWFR",
    "0B3OXLFB0LXMZUME8BO1",
    "Q7XXOPVYV2LTMW4GP2X8",
    "URXFQ2C9F5ADSYAB1YV5",
    "H8FS3AELJYS88ZJH6WV0",
    "5BUK0OY695TCCQ9M9JQF",
    "DREFTZMMKWJS02KEAA1B",
    "LVEGE47UC042AU5XGNOQ",
    "V9DGQ9TJ7U5TR0GCGLK6",
    "XDNHLGF1UELN5VR6CMS3",
    "ZIH42VVMXC8JNPWGQA7E",
    "OOGBI9CDCVR0PR4IQRT1",
    "77XDTYPVLWXYDHITZHRS",
    "2UNMNXEIVN0CAO6II167",
    "7W4U1ONPOM1YHL2DN750",
    "P9LLV23EOFLANSAYGLPI",
    "1YW45DZOS1L7J33U3Q9M",
    "HGM1WB8KQ4LGSEUXB9VZ",
    "1ZYTFI1D9ZKRPR9JRIBF",
    "RMM6GCB4IQ7EWAEWDIGF",
]

# how many times each LEI appears in our fake dataset. 450 total records
number_of_occurences = [
    2,
    18,
    9,
    16,
    4,
    1,
    15,
    7,
    42,
    45,
    44,
    13,
    32,
    30,
    24,
    49,
    7,
    46,
    18,
    28,
]

# this will contain 450 LEIs. Essentially a dot product between leis
# and number of occurrences.
repeated_leis = []
for _, lei in enumerate(leis):
    repeated_leis += [lei] * number_of_occurences[_]

# create a mock postgres dataframe
mock_pg_lar_data = pd.DataFrame({"row_number": np.arange(450)})

# application date and action taken date are also required by the
# function that processes LAR partitions. Otherwise a key error is
# raised
mock_pg_lar_data["action_taken_date"] = "20230608"
mock_pg_lar_data["application_date"] = "20221212"

mock_pg_lar_data["lei"] = repeated_leis

# corresponding lar_row_counts_by_lei dataframe
lar_row_counts_by_lei = pd.DataFrame({"lei": leis, "count": number_of_occurences})
