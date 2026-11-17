# Testing SmartBite

The automated test suite uses Python's built-in `unittest`, so there is nothing extra to install.
It needs **no live AI connection, no API key and no internet access**: the AI is replaced by a scripted
fake model, Open Food Facts by a fake searcher, and all data files are written to throw-away temp folders
(your real `data/` folder is never touched).

## Run inside Docker (recommended / how the assessor runs it)

From the project root:

```bash
docker build -t smartbite .
docker run --rm smartbite python -m unittest discover -s tests -t . -v
```

Expected with the current project: `Ran 231 tests ... OK (skipped=1)` on a headless Docker container. The Tkinter GUI module is intentionally skipped when no display server is available; all non-GUI tests execute. The exact count may change as tests are added.

**GUI test note:** `tests/test_gui.py` creates real Tkinter windows. It runs on a machine with a graphical display, but is skipped on a headless Linux container. If the assessor requires GUI tests to execute inside Docker too, a display server such as Xvfb must be configured separately.

## Run without Docker

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -t . -v
```

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
