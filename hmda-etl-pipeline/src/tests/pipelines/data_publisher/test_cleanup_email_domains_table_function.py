"""
Verify the helper function cleanup_email_domains_table works as expected.
"""

import pandas as pd

from hmda_etl_pipeline.pipelines.data_publisher.nodes import cleanup_email_domains_table


def test_cleanup_email_domains_table():
    """Verify that the helper function cleanup_email_domains_table
    cleans up and consolidates all email domains into a list of distinct
    email domains in a single row per lei.
    """

    # Create test table with duplicated email domains and extra whitespace
    test_table = [
        [1, "bank1", "bank1.com"],
        [2, "bank1", "bank1.com,abcbank.com"],
        [3, "bank1", "bank1.com, abcbank.com"],
        [4, "bank1", "bank1.com,abcbank.com, defbank.com"],
        [5, "bank1", "bank1.com, abcbank.com, defbank.com"],
        [6, "bank2", "xzybank.com, xzy.com"],
        [7, "bank2", "xzy.com, xzybank.com"],
        [8, "bank3", "mybank.com"],
    ]
    test_table_df = pd.DataFrame(test_table, columns=["id", "lei", "email_domain"])

    # Epected result table has no duplicates and no extra whitespace
    expected_table = [
        ["bank1", "bank1.com, abcbank.com, defbank.com"],
        ["bank2", "xzybank.com, xzy.com"],
        ["bank3", "mybank.com"],
    ]
    expected_table_df = pd.DataFrame(expected_table, columns=["lei", "email_domain"])

    # Verify that the table matches the expected result
    assert cleanup_email_domains_table(test_table_df).equals(expected_table_df)
