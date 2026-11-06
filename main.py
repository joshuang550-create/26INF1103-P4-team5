from app.engine import AppEngine
from models.errors import as_app_error


def main():
    try:
        engine = AppEngine()
    except Exception as error:
        problem = as_app_error(error)
        print(problem)
        return



    engine.login("Mary", "mary")


    print(engine.profile.username)              # mary
    print(engine.profile.age)                   # 22
    print(engine.profile.bmi)                   # 23.44
    print(engine.profile.country)               # singapore
    print(engine.profile.ethnicity)             # chinese
    print(engine.profile.medical_conditions)    # ['high cholesterol', 'high blood pressure', 'tmj']


    engine.update_age(50)
    print(engine.profile.age)                   # 50


    engine.remove_medical_conditions([1, 2])
    print(engine.profile.medical_conditions) # ['high cholesterol']


    user_inputs_these_conditions_in_the_gui = ["Type 1 Diabetes", "hypertension"]
    for condition in user_inputs_these_conditions_in_the_gui:
        if engine.is_valid_condition(condition): # engine.is_valid_condition() checks 1 condition at a time, so need to loop through the list. dont do it like this, this is just example. got much better way to do it
            continue
        else:
            return # use rapidfuzz to guess what the user was trying to enter, if all the ratios are below like 50%, just default to something like "please enter a valid medical condition." (note that 'diabetes' should match 'Type 1 Diabetes', even if ratio is low, maybe use regex?)
    engine.add_medical_conditions(user_inputs_these_conditions_in_the_gui)


    print(engine.profile.medical_conditions) # ['high cholesterol', 'type 1 diabetes', 'hypertension']


    outcome = engine.check_food("banana")
    print(outcome)

    print(outcome.needs_answers) # if true, need ask follow up questions to user, get their answer, then reprompt.

    print(outcome.questions) # these are the questions to ask the user
    print(outcome.outcome) # Outcome object from logic manager

    print(outcome.outcome.headline) # UNDETERMINED means confidence_score not good so generic fallback food recommendation response. OK/CAUTION/AVOID means AI was confident enough.
    print(outcome.outcome.severity) # the verdict. 0=OK, 1=CAUTION, 2=AVOID
    print(outcome.outcome.details()) # this contains the long text you will show the user in the GUI. maybe can consider a donut chart showing the confidence score? green if high, yellow mid, no red since low means UNDETERMINED    this is what it looks like - {'reason': 'You are considering a medium raw banana weighing about 118 grams. Because you have diabetes and type 1 diabetes, the natural sugars in this fruit will raise your blood sugar and must be counted in your daily carbohydrate management. The fruit is very low in sodium and fat, which supports your high cholesterol and hypertension.', 'portion_g': 118, 'nutrients': {'sodium_mg': 1.2, 'sugar_g': 14.4, 'saturated_fat_g': 0.1, 'trans_fat_g': 0.0}, 'flags': [{'nutrient': 'sugar_g', 'value': 14.4, 'level': 'moderate'}], 'allergens_found': {}, 'potential_concern': True, 'confidence': 9.0}


    assume_the_ai_asks_follow_up_questions = {"How is the banana prepared? (raw, boiled etc.)": "", "Is the banana yellow or green?": ""} # outcome.questions will show u this. ask the user to answer these questions in the GUI
    user_will_then_answer_the_questions_in_the_gui = {"How is the banana prepared? (raw, boiled etc.)": "raw", "Is the banana yellow or green?": "yellow"} # once they answer and submit, add their answers to the outcome.questions dict and send it to engine.answer_questions()
    outcome = engine.answer_questions(user_will_then_answer_the_questions_in_the_gui) # if more the ai has more questions, repeat, if not, you can show the outcome to the user in the GUI.

    print(outcome.outcome.headline)
    print(outcome.outcome.severity)
    print(outcome.outcome.details())


    engine.logout()


if __name__ == "__main__":
    main()
