"""Small, self-contained input checks for AdaptFit forms.

Nothing else in AdaptFit imports this file yet, so adding it cannot change
how the app behaves. Later, the profile form or API can call these helpers.
"""


def validate_number_in_range(value, low, high, label, optional=True):
    """Check that value is a number between low and high.

    Returns (True, "") when it is fine, or (False, "message") when it is not.
    """
    if value is None or str(value).strip() == "":
        if optional:
            return True, ""
        return False, f"{label} is required."
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False, f"{label} must be a number."
    if number < low or number > high:
        return False, f"{label} must be between {low} and {high}."
    return True, ""


def validate_choice(value, allowed, label, optional=True):
    """Check that value is one of the allowed choices (ignoring capitals).

    Returns (True, "") when it is fine, or (False, "message") when it is not.
    """
    if value is None or str(value).strip() == "":
        if optional:
            return True, ""
        return False, f"{label} is required."
    if str(value).strip().lower() not in [item.lower() for item in allowed]:
        return False, f"{label} must be one of: {', '.join(allowed)}."
    return True, ""