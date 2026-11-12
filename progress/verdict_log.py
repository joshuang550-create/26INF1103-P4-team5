import json
import time
from contextlib import suppress
from pathlib import Path

from models.errors import DataError

Default_Path = Path(__file__).resolve().parent.parent / "data" / "verdict_log.json"


class VerdictLog:
    """ Rmbs verdict of every food checked per user in a json"""

    def __init__(self, path=Default_Path):
        self._path = Path(path)

    # =========== Public Methods ===========
    def add(self, username, food_name, verdict):
        log = self._read()
        entries = log.get(username)
        if not isinstance(entries, list):
            entries = []
        entries.append({"time": time.time(), "food": food_name, "verdict": verdict})
        log[username] = entries
        self._write(log)

    def entries(self, username):
        """ (timestamp, verdict) pair for user, oldest first """
        raw = self._read().get(username, [])
        if not isinstance(raw, list):
            return []
        return [(entry["time"], entry["verdict"]) for entry in raw
                if isinstance(entry, dict) and isinstance(entry.get("time"), (int, float)) and "verdict" in entry]

    def verdicts(self, username):
        """ verdict names for user, oldest first - e.g. OK, AVOID, CAUTION """
        return [verdict for _timestamp, verdict in self.entries(username)]

    def delete(self, username):
        log = self._read()
        if username in log:
            del log[username]
            self._write(log)

    # =========== Private Methods ===========
    def _read(self):
        try:
            with self._path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return {} # first run, nth saved yet
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise DataError("Progress history is corrupted, nothing has been changed.") from error
        except OSError as error:
            raise DataError("Progress history could not be read.") from error

        if not isinstance(data, dict):
            raise DataError("Progress history is corrupted, nothing has been changed.")
        return data

    def _write(self, log):
        temp = self._path.with_name(self._path.name + ".tmp") # write to a temp file first so a crash cannot leave half-written data
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with temp.open("w", encoding="utf-8") as file:
                json.dump(log, file, indent=4)
            temp.replace(self._path)
        except OSError as error:
            with suppress(OSError):
                temp.unlink(missing_ok=True)
            raise DataError("The progress history could not be saved.") from error
    