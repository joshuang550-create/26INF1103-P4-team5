from app.app_engine import AppEngine
from exceptions.as_app_error import as_app_error


def main():
    try:
        engine = AppEngine()
    except Exception as error:
        problem = as_app_error(error)
        print(problem) # dont keep as print(), the GUI should show a popup, then once the user clicks the close button in the popup, the whole app will terminate cleanly.
        return


if __name__ == "__main__":
    main()
