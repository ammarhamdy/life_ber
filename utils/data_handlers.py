from typing import Dict


def safe_get(obj: Dict, *keys, default=None):
    """Safely navigate nested dictionary keys"""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, {})
        else:
            return default
    return obj if obj != {} else default