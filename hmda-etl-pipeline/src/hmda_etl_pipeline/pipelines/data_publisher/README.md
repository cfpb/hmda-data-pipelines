# Pipeline data_publisher

TODO: THIS NEEDS TO BE WRITTEN 

## Overview

<!---
Please describe your modular pipeline here.
-->

## Pipeline inputs

<!---
The list of pipeline inputs.
-->

## Pipeline outputs

<!---
The list of pipeline outputs.
-->

### analyzed_mlar_flat_file

This file is a copy of the annual **modified_lar_flat_file** with one appended **Analysis** column. Processing runs check functions on selected fields in the modified_lar_flat_file according to the configuration given in **data_publisher.yml**. Record field values which produce positive test results are noted in the Analysis column for the record with **markers**. Markers have the following format:

```
{ddd}{m1}[{m2}[{m3}...]
```

Here **{ddd}** denotes a three-digit number for the field according to its order in the CSV file, and each **{mN}** denotes a single-character marker indicating a positive test result for the record field value. Multiple characters after the three-digit field identifier indicate multiple positive test results for that field. Markers are concatenated in the Analysis column, so a record with positive test results for multiple fields could appear as follows:

```
089X022oO
```

This Analysis value indicates an "X" marker for field 89 and "o" and "O" markers for field 22.

The following check functions are available.

| **Check Function** | **Marker** | **Description** |
| --- | --- | --- |
| check_invalidity | X | Marks values which are invalid for a given field. |
| check_high_values | H | Marks values equal to or exceeding a configured field threshold. |
| check_low_values | L | Marks values equal to or below a configured field threshold. |
| check_lender_nulls | n | Marks all null (missing) field values for a lender if the quantity of null values equals or exceeds a configured percentage of all lender records. |
| check_year_nulls | N | Marks all null (missing) field values for all lenders if the quantity of null values equals or exceeds a configured percentage of all records for all lenders for a given year. |
| check_lender_outliers | o | Marks values above or below a configured multiple of standard deviations from the mean field value for all lender records. |
| check_year_outliers | O | Marks values above or below a configured multiple of standard deviations from the mean field value for all records for all lenders for a given year. |
| check_lender_repeaters | r | Marks all field values within a 1% range if the quantity of values in that range equals or exceeds a configured percentage of all lender records. |
| check_year_repeaters | R | Marks all field values within a 1% range if the quantity of values in that range equals or exceeds a configured percentage of all records for all lenders for a given year. |
