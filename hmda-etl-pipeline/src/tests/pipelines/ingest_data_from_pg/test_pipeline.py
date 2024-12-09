"""
Verify the chunking logic of LAR data with an emphasis on ensuring the
number of partitions is correctly determined and verifying that no rows
of data are lost / generated.
"""

import os
import tempfile

import pandas as pd
import pytest
from hmda_etl_pipeline.pipelines.ingest_data_from_pg.nodes import process_lar_partitions
from pandas.io.parsers import TextFileReader

from .mock_lar_generation import lar_row_counts_by_lei, mock_pg_lar_data


def create_lar_iterator(chunksize: int) -> TextFileReader:
    """Writes mock_pg_lar_data to disc and reads said data using
    Pandas read_csv with chunksize specified. This replicates the
    behavior of reading data from Postgres with chunksize specified.

    Args:
        chunksize (int): Number of rows that should be returned per
            chunk of mock_pg_lar_data.

    Returns:
        TextFileReader: An iterator of Pandas DataFrames. The
            union of these dataframes is mock_pg_lar_data.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        # this only exists for the life of this "with" statement
        temp_path_to_csv = os.path.join(tempdir, "mock_lar.csv")

        # write file to disc
        mock_pg_lar_data.to_csv(temp_path_to_csv, index=False)

        # read the file with chunksize specified to create an iterator
        chunked_data = pd.read_csv(temp_path_to_csv, header=0, chunksize=chunksize)

    return chunked_data


# See the following for a description of this pattern
# https://docs.pytest.org/en/6.2.x/fixture.html#factories-as-fixtures
@pytest.fixture()
def lar_iterator_factory():
    return create_lar_iterator


def test_no_rows_are_lost(lar_iterator_factory):
    """Verify that write_partitioned_lar does not lost any rows of data.

    This test verifies the logic of write_partitioned_lar to ensure that
    this function correctly determines the chunksize from the first
    sample of data and how many partitions should be created."""

    # an iterator of mock lar data where each chunk has 20 rows
    # the last chunk only has 10
    lar_iterator = lar_iterator_factory(chunksize=20)

    dict_of_chunks = process_lar_partitions(
        pg_lar_data=lar_iterator,
        lar_row_counts_by_lei=lar_row_counts_by_lei,
        column_dtypes={},
        count_verification_passed=True,
    )

    data_holder = []

    for _, loader in dict_of_chunks.items():
        data_holder.append(loader())

    # verify that no rows are lost
    concatenated_df = pd.concat(data_holder)

    assert set(concatenated_df.row_number) == set(mock_pg_lar_data.row_number)


def test_chunksize_larger_than_number_of_rows_in_raw_data(lar_iterator_factory):
    """A single chunk of data is returned with all rows when chunksize
    exceeds the number of rows in the dataset."""

    # setting the chunksize to one larger than the number of rows in mock_pg_lar_data
    lar_iterator = lar_iterator_factory(chunksize=mock_pg_lar_data.shape[0] + 1)

    dict_of_chunks = process_lar_partitions(
        pg_lar_data=lar_iterator,
        lar_row_counts_by_lei=lar_row_counts_by_lei,
        column_dtypes={},
        count_verification_passed=True,
    )

    assert dict_of_chunks["lar_0"]().shape == (450, 4)
    assert "lar_1" not in dict_of_chunks


def test_chunksize_equal_to_number_of_rows_in_raw_data(lar_iterator_factory):
    """A single chunk of data is returned with all rows when chunksize
    is exactly equal to the number of rows in the dataset."""

    # setting the chunksize equal to the number of rows in mock_pg_lar_data
    lar_iterator = lar_iterator_factory(chunksize=mock_pg_lar_data.shape[0])

    dict_of_chunks = process_lar_partitions(
        pg_lar_data=lar_iterator,
        lar_row_counts_by_lei=lar_row_counts_by_lei,
        column_dtypes={},
        count_verification_passed=True,
    )

    assert dict_of_chunks["lar_0"]().shape == (450, 4)
    assert "lar_1" not in dict_of_chunks
