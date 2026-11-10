import json
import time
from pathlib import Path


class VerdictLog:
    """ Rmbs verdict of every food checked per user in a json"""

    def __init__(self, path="data/verdict_log.json"):
        self.path = Path(path)

    # =========== Public Methods ===========
    def add(self, username, food_name, verdict):
        log = self._read()
        entries = log.get(username)
        if not isinstance(entries, list):
            entries = []
        entries.append({"time": time.time(), "food": food_name, "verdict": verdict})
        log[username] = entries
        self._write(log)

    def verdicts(self, username):
        """ Verdict names for user, oldest first, e.g. ["OK", "AVOID", "CAUTION"]"""
        entries = self.read().get(username, [])
        if not isinstance(entries, list):
            return []
        return [entry["verdict"] for entry in entries if isinstance(entry, dict) and "verdict" in entry]

    # =========== Private Methods ===========
    def _read(self):
        try:
            with self._path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {} # missing or corrupt file, start empty
        return data if isinstance(data, dict) else {}

    def _write(self, log):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as file:
            json.dump(log, file, indent=4)
    