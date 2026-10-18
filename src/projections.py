"""Calendar-aware labels and defaults within the supported projection horizon."""

from datetime import date


def nextCalendarYear(currentYear: int | None = None) -> int:
    """Return the next calendar year, with an explicit year for deterministic tests."""
    return (date.today().year if currentYear is None else currentYear) + 1


def preferredProjectionYear(firstYear: int, lastYear: int, currentYear: int | None = None) -> int:
    """Prefer next year; fall back to the nearest supported year outside the horizon."""
    if firstYear > lastYear:
        raise ValueError("The projection horizon must contain at least one year.")
    return min(max(nextCalendarYear(currentYear), firstYear), lastYear)


def projectionYearLabel(year: int, currentYear: int | None = None) -> str:
    """Identify next year accurately without labeling another projection as next year."""
    return f"{year} (next year)" if year == nextCalendarYear(currentYear) else f"{year} (projected)"
