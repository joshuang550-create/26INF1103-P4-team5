# Testing SmartBite

The automated test suite uses Python's built-in `unittest`, so there is nothing extra to install.
It needs **no live AI connection, no API key and no internet access**: the AI is replaced by a scripted
fake model, Open Food Facts by a fake searcher, and all data files are written to throw-away temp folders
(your real `data/` folder is never touched).

## Run ALL tests inside Docker (core logic + real Tkinter GUI)

From the project root (PowerShell, VS Code terminal, or any shell with Docker):

```bash
docker build --no-cache -t smartbite .
docker run --rm -e SMARTBITE_REQUIRE_GUI_TESTS=1 smartbite xvfb-run -a python -m unittest discover -s tests -t . -v
```

`xvfb-run -a` starts a virtual graphical screen within the container. This
allows all **66 GUI tests** to create actual Tkinter windows even on a headless
Docker host. The Dockerfile installs `tk`, `xvfb`, `xauth` and a default font.
`SMARTBITE_REQUIRE_GUI_TESTS=1` ensures a missing/broken virtual display is
reported as a **failure**, not a silently skipped GUI test module.

At the time of this update the project contains **231 non-GUI tests and 66 GUI
tests (297 total)**. Expected result if nothing else changes: `Ran 297 tests ... OK`
with **no GUI skips**. Counts can change when tests are added or removed.

The same command is used by `.github/workflows/automated_test_suite.yml` on
GitHub Actions (with the image name `smartbite:test`). GitHub must contain the
committed Dockerfile, workflow and test changes.

### Run only GUI tests

```bash
docker run --rm -e SMARTBITE_REQUIRE_GUI_TESTS=1 smartbite xvfb-run -a python -m unittest tests.test_gui -v
```

### Run core tests without a display

```bash
docker run --rm smartbite python -m unittest discover -s tests -t . -v
```

This last command intentionally skips the GUI module when no display exists;
**do not use it as evidence that the GUI tests passed**.

## Run without Docker

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -t . -v
```

For GUI coverage on headless Linux outside Docker, install Xvfb and run:
`xvfb-run -a python -m unittest discover -s tests -t . -v`.

Run a single file or test:

```bash
python -m unittest tests.test_logic_manager -v
python -m unittest tests.test_engine.FoodCheckVerdictTests.test_allergen_overrides_everything_and_skips_reprompt
```

## What is covered

| Requirement | Where |
|---|---|
| Core logic and important class behaviour | `test_logic_manager.py`, `test_user_profile.py`, `test_engine.py`, `test_ai_manager.py` |
| Runs without a live AI (samples, mocks, stubs) | `tests/helpers.py` (`FakeModel`, `FakeSearcher`, `ai_reply()`), `test_ai_models.py` (mocked Gemini client) |
| Business rules (severity to verdict, allergen override, thresholds, boundaries) | `test_logic_manager.py`, `FoodCheckVerdictTests` in `test_engine.py` |
| Scoring / routing (confidence, reprompt, fallback, follow-up questions, round limit) | `ConfidencePolicyTests`, `ConfidenceRoutingTests`, `FollowUpQuestionTests` |
| Response validation | `test_ai_response_validator.py` |
| New features (barcode lookup, fallback recommendations, follow-up questions, profile editing) | `test_openfoodfacts.py`, `InputValidationTests`, `ProfileEditingTests`, `AccountTests` |
| Failure cases: malformed AI output | `test_ai_response_validator.py`, `MalformedAIOutputTests`, `AIManagerTests` |
| Failure cases: missing / corrupt persistence files, unwritable folders, bad API key | `test_data_manager.py` (`CorruptFileTests`, `LookupFileTests`, `ApiKeyTests`) |
| Failure cases: AI / network errors | `test_ai_models.py`, `test_errors.py` |

## Updated feature coverage

The current project also tests progress tracking (`tests/test_progress.py`): saving verdict history for individual users, continuing checks after follow-up questions, trend scoring, weekly breakdowns, chart fallback behaviour, corrupted/missing history files, persistence after reopening, and atomic-write failures.

The tests use `tempfile` and fakes; they do not read or change personal data under the project `data/` folder and do not require a real AI connection.
