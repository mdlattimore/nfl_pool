def find_paths(data, target_key, path=None):
    """Find all paths to target_key in nested dicts/lists."""
    if path is None:
        path = []

    results = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = path + [f"['{key}']"]
            if key == target_key:
                results.append("".join(new_path))
            results.extend(find_paths(value, target_key, new_path))

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            new_path = path + [f"[{idx}]"]
            results.extend(find_paths(item, target_key, new_path))

    return results

