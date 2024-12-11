import pytest

from assess.shared.filters import (
    all_caps_to_human,
    assess_datetime_format,
    datetime_format_24hr,
    format_address,
    format_date,
    format_project_ref,
    remove_dashes_underscores_capitalize,
    remove_dashes_underscores_capitalize_keep_uppercase,
    slash_separated_day_month_year,
)


class TestFilters(object):
    def test_datetime(self):
        time_in = "2023-01-30T12:00:00"
        result = assess_datetime_format(time_in, "%d %B %Y at %H:%M")
        assert "30 January 2023 at 12:00pm" == result, "Wrong format returned"

    def test_caps_to_human(self):
        word_in = "HELLO WORLD"
        result = all_caps_to_human(word_in)
        assert "Hello world" == result, "Wrong format returned"

    def test_slash_separated_day_month_year(self):
        date_in = "2023-01-30T12:00:00.500"
        result = slash_separated_day_month_year(date_in)
        assert "30/01/23" == result, "Wrong format returned"

    def test_24hr_datetime(self):
        date_in = "2023-01-30T14:50:00.500"
        result = datetime_format_24hr(date_in)
        assert "30/01/2023 at 14:50" == result, "Wrong format returned"

    def test_format_project_ref(self):
        short_id = "COF-123-LKMBNS"
        result = format_project_ref(short_id)
        assert "LKMBNS" == result, "Wrong format returned"

    @pytest.mark.parametrize(
        "address, expected",
        [
            (
                "Test Address, null, Test Town Or City, null, QQ12 7QQ",
                ["Test Address", "Test Town Or City", "QQ12 7QQ"],
            ),
            (
                "null, Test Address, Test Town Or City, null, QQ12 7QQ",
                ["Test Address", "Test Town Or City", "QQ12 7QQ"],
            ),
            (
                "Test Address, null, Test Town Or City, null, null",
                ["Test Address", "Test Town Or City"],
            ),
            (
                "null, Test Address, null, Test Town Or City, null, null",
                ["Test Address", "Test Town Or City"],
            ),
            (
                "Test Address, Test Town Or City, QQ12 7QQ",
                ["Test Address", "Test Town Or City", "QQ12 7QQ"],
            ),
        ],
    )
    def test_format_address(self, address, expected):
        assert format_address(address) == expected

    @pytest.mark.parametrize(
        "address, expected",
        [
            (
                "test-string_with-dashes_and_underscores",
                "Test string with dashes and underscores",
            ),
            (
                "test_string_with_underscores_only",
                "Test string with underscores only",
            ),
            ("test-string-with-dashes-only", "Test string with dashes only"),
            (
                "teststringwithnodashesornunderscores",
                "Teststringwithnodashesornunderscores",
            ),
        ],
    )
    def test_fremove_dashes_underscores_capitalize(self, address, expected):
        assert remove_dashes_underscores_capitalize(address) == expected

    @pytest.mark.parametrize(
        "address, expected",
        [
            (
                "string_with_UPPERCASE_words-and-underscores_and-dashes",
                "String with UPPERCASE words and underscores and dashes",
            ),
            (
                "string with UPPERCASE words only",
                "String with UPPERCASE words only",
            ),
            (
                "test_string_with_underscores_only",
                "Test string with underscores only",
            ),
            ("test-string-with-dashes-only", "Test string with dashes only"),
            (
                "teststringwithnodashesornunderscores",
                "Teststringwithnodashesornunderscores",
            ),
        ],
    )
    def test_remove_dashes_underscores_capitalize_keep_uppercase(self, address, expected):
        assert remove_dashes_underscores_capitalize_keep_uppercase(address) == expected


@pytest.mark.parametrize(
    "input_date, from_format, to_format, expected_output",
    [
        (
            "2023-06-06T13:38:51.467199",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%d/%m/%Y at %H:%M",
            "06/06/2023 at 13:38",
        ),
        ("2023-06-06 13:38:51", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "06/06/2023"),
        ("06-06-2023", "%d-%m-%Y", "%Y/%m/%d", "2023/06/06"),
    ],
)
def test_format_date(input_date, from_format, to_format, expected_output):
    assert format_date(input_date, from_format, to_format) == expected_output
