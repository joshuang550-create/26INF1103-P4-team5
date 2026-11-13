from app.engine import AppEngine
from progress.tracking_engine import ProgressTrackingEngine
from progress.verdict_log import VerdictLog
from gui.app import SmartBiteApp


def main():
    engine = ProgressTrackingEngine(AppEngine(), VerdictLog()) # same API as AppEngine, plus charts
    SmartBiteApp(engine).mainloop()


if __name__ == "__main__":
    main() # add to terminal env vars -    $env:FERNET_SECRET_KEY="vYTFX1ni17MptleqMTz1hCspMZEaqlaLPG91boo55-Q="
