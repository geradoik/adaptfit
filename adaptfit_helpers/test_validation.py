from validation import validate_choice, validate_number_in_range


def test_empty_optional_number_is_ok():
    assert validate_number_in_range("", 500, 10000, "Calorie intake") == (True, "")


def test_number_inside_range_is_ok():
    assert validate_number_in_range("2200", 500, 10000, "Calorie intake") == (True, "")


def test_number_outside_range_is_rejected():
    ok, message = validate_number_in_range("50", 500, 10000, "Calorie intake")
    assert ok is False
    assert "between 500 and 10000" in message


def test_text_instead_of_number_is_rejected():
    ok, message = validate_number_in_range("abc", 500, 10000, "Calorie intake")
    assert ok is False
    assert "must be a number" in message


def test_required_number_missing_is_rejected():
    result = validate_number_in_range("", 0, 10, "Weight", optional=False)
    assert result == (False, "Weight is required.")


def test_valid_choice_is_ok_even_with_capitals():
    assert validate_choice("Moderate", ["mild", "moderate", "aggressive"], "Deficit level") == (True, "")


def test_unknown_choice_is_rejected():
    ok, message = validate_choice("extreme", ["mild", "moderate"], "Deficit level")
    assert ok is False
    assert "must be one of" in message


def test_empty_optional_choice_is_ok():
    assert validate_choice("", ["mild", "moderate"], "Deficit level") == (True, "")