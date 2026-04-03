"""Shared utilities for the content agent runtime."""
from datetime import datetime


def current_season() -> str:
    month = datetime.now().month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"
