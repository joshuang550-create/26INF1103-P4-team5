from datetime import datetime, timedelta

VERDICTS = ("OK", "CAUTION", "AVOID")


class WeeklyBreakdown:
    """ Count verdict per week (start monday) from (timestamp, verdict) pairs. """

    def __init__(self, entries, max_weeks=8):
        self._max_weeks = max_weeks
        self._weeks = self._group(entries)

    @property
    def weeks(self):
        """[(monday, {"OK":2, "CAUTION": 1, "AVOID": 0}), ...] oldest first, weeks with no checks included. """
        return [(monday, dict(counts)) for monday, counts in self._weeks]

    def summary(self):
        """A plain-English description of the weeks, for when the chart cannot be shown."""
        if not self._weeks:
            return "No food checks yet. Check a food to start your progress history."

        totals = {name: sum(counts[name] for _monday, counts in self._weeks) for name in VERDICTS}
        latest_monday, latest = self._weeks[-1]
        return (f"Over the last {len(self._weeks)} week{'' if len(self._weeks) == 1 else 's'} you made "
                f"{sum(totals.values())} food checks: {totals['OK']} OK, {totals['CAUTION']} CAUTION and {totals['AVOID']} AVOID. "
                f"The week starting {latest_monday.strftime('%d %b')} had "
                f"{latest['OK']} OK, {latest['CAUTION']} CAUTION and {latest['AVOID']} AVOID.")

    # ========== Private Methods ==========
    def _group(self, entries):
        by_week = {}
        for timestamp, verdict in entries:
            if verdict not in VERDICTS:
                continue
            day = datetime.fromtimestamp(timestamp).date()
            monday = day - timedelta(days=day.weekday())
            counts = by_week.setdefault(monday, {name: 0 for name in VERDICTS})
            counts[verdict] += 1

        if not by_week:
            return []

        weeks = []
        monday = min(by_week)
        while monday <= max(by_week): 
            weeks.append((monday, by_week.get(monday, {name: 0 for name in VERDICTS})))
            monday += timedelta(weeks=1)
        return weeks[-self._max_weeks:]

