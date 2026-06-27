def merge_user_data(existing: dict, new_data: dict) -> dict:
    # Bug 1: mutates input
    result = existing
    for key in new_data:
        # Bug 2: overwrites nested dicts incorrectly
        if key in result and isinstance(result[key], dict):
            result[key] = new_data[key]
        else:
            result[key] = new_data[key]
    return result
