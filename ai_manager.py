"""Core engine of the application.
"""


def generate_prompt():
    # idea is for this function to output a single text string prompt that will be sent to the AI.
    # this function should take in data such as: user's profile info like medical conditions and also take in the food item the user wants to check.
    # the prompt can be stored like this: f"I am a {profile_age} year old {profile_gender} from {profile_country}. I have {profile_medical_conditions}. Give me a risk assessment of eating {user_input_food}. Provide a confidence score based on factual data for every piece of information you give me. ...
    pass


def prompt_ai():
    # pass the text string prompt and AI API to this function to send to the API.
    # returns a JSON formatted AI response.
    pass


def check_response_schema():
    # takes in the JSON ai response to check if it is correctly formatted. eg. if the keys are all correct, and the values are all the right data type.
    pass


def calculate_response_confidence():
    # From the JSON response, take the key-value pairs that store all the confidence/risk scores and do some math to calculate an overall respose confidence score from 0.0 to 10.0
    pass


