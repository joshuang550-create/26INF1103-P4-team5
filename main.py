from app.engine import AppEngine
from models.errors import as_app_error


def main():
    try:
        engine = AppEngine()
    except Exception as error:
        problem = as_app_error(error)
        print(error)
        print(problem) # dont keep as print(), the GUI should show a popup, then once the user clicks the close button in the popup, the whole app will terminate cleanly.
        return


    engine.login("mary", "mary")

    print(f"\n\nMedical Conditions: {engine.profile.medical_conditions}\n\n")

    outcome = engine.check_food("one standard bowl of prawn noodles with soup. yellow noodles. and i will finish the whole bowl.")



    print(f"Outcome: {outcome}\n\n")
    print(f"Questions: {outcome.questions}\n\n\n\n")

    print(f"Headline: {outcome.outcome.headline}\n\n")
    print(f"Severity: {outcome.outcome.severity}\n\n")
    print(f"Details: {outcome.outcome.details()}\n\n")











if __name__ == "__main__":
    main()
