""" Starts the SmartBite desktop GUI:  python run_gui.py

Kept separate from main.py so the headless CI step (python main.py) and Docker are unaffected. """
from app.engine import AppEngine
from progress.tracking_engine import ProgressTrackingEngine
from progress.verdict_log import VerdictLog
from gui.app import SmartBiteApp


def main():
    engine = ProgressTrackingEngine(AppEngine(), VerdictLog()) # same API as AppEngine, plus charts
    SmartBiteApp(engine).mainloop()


if __name__ == "__main__":
    main()