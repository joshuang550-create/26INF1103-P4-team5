"""Core engine of the application.
"""


def generate_prompt():
    # idea is for this function to output a single text string prompt that will be sent to the AI.
    # this function should take in data such as: user's profile info like medical conditions and also take in the food item the user wants to check.
    # the prompt can be stored like this: f"I am a {profile_age} year old {profile_gender} from {profile_country}. I have {profile_medical_conditions}. Give me a risk assessment of eating {user_input_food}. Provide a confidence score based on factual data for every piece of information you give me. ...
    # note that the prompt should include a line like this: "If you need more information about me, instead of giving me the full response JSON, give me a JSON file where each key is a piece of information you require, and the values are empty strings that i will fill up. I will then send this JSON file back to you, after which you can send me the final full response JSON file. Should you need to clarify things or ask for more information, we will repeat this process until you are satisfied, just ensure that your request JSON file is always with empty values that i will fill in, no adding on to previous information."
    pass


def prompt_ai():
    # pass the text string prompt and AI API to this function to send to the API.
    # returns a JSON formatted AI response     OR     a JSON formatted request for more information. Ensure we keep the formatting identical throughout so the user input will just be filled into each key-value pair in the JSON file and sent straight back to the AI.
    pass


def check_response_type():
    # to keep to the requirement of 1 function do 1 thing. i separated this function from check_response_schema()
    # this function will be run immediately after prompt_ai(), before check_response_schema().
    # this function will check if the JSON response from the ai is a full response or a request for more information.
    # the check can be done by seeing if all the values are empty strings "". (I can see potential issues with this check but not sure what else would work better. Maybe in the end need the ai to respond with not just 1 JSON file but a text saying Response/Request.)
    # if reponse_type == "request" then call print_follow_up_request_input() then generate_follow_up_prompt() then prompt_ai(). as many times as needed.
    # if response_type == "response" then call check_response_schema() then calculate_response_confidence(). ...
    pass


def check_response_schema():
    # takes in the JSON ai response to check if it is correctly formatted. eg. if the keys are all correct, and the values are all the right data type. (maybe we can create a predefined template that we send with the prompt.)
    # if the check returns that the JSON is malformed/errornous, we have to decide if we want to regenerate the prompt and try a new one, or create a function that will generate a prompt specifying the error.
    # i am thinking that we can do something like: if key == "Risk Score" and value != float then return f"The {key}'s value you provided in the response JSON file was not a float datatype. Please amend this error and comply with the template provided."
    pass


def generate_follow_up_prompt():
    # send this string output to prompt_ai() same as before. Only thing to note is how to handle the chat session, make sure u stay in the same session.
    pass



import json
from openai import OpenAI
#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
from openai import OpenAI

#client = OpenAI(
    #api_key="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"
#)

from cryptography.fernet import Fernet
from openai import OpenAI
