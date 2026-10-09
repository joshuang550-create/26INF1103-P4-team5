"""Food risk analysis with a persistent Gemini chat session per user.
Only input: menu choice. Foods are hard-coded test data."""
import json
import os
import time
from cryptography.fernet import Fernet
from google import genai
from google.genai import types
from openfoodfacts_prompt import build_food_prompt

MODEL_NAME = "gemini-3.5-flash-lite"
CHATS_FILE = "chats.json"

PROFILES_FILE = "user_profiles.json"


def load_profiles(path=PROFILES_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def choose_username(profiles):
    names = ", ".join(profiles)
    while True:
        name = input(f"Username ({names}): ").strip()
        for valid in profiles:
            if valid.lower() == name.lower():
                return valid
        print("Unknown user.")

PROFILES = {
    "John": {
        "username": "John",
        "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
        "gender": "male", "age": 40, "race": "indian", "country": "india",
        "height": 170.0, "weight": 70.0,
    },
    "ride": {
        "username": "ride",
        "password_hash": "e049bd056f936d1b39b704abcf824eaef39bd8877fcbb82b2a213ceec82bdf26",
        "gender": "male", "age": 22, "race": "caucasian", "country": "Singapore",
        "height": 190.0, "weight": 80.0,
        "medical_conditions": ["diabetes", "high blood pressure", "peanut allergy"],
    },
}

# Hard-coded test foods. Each "New chat" checks the next one in the list.
#TEST_FOODS = [
    #{"food_name": "Chocolate Protein Bar", "ingredients": ["whey protein", "maltitol", "peanuts", "caffeine"]},
    #{"food_name": "Teh Tarik", "ingredients": ["black tea", "condensed milk", "sugar"]},
    #{"food_name": "Chicken Rice", "ingredients": ["chicken", "rice", "soy sauce", "chilli sauce"]},
#]
TEST_FOODS = [
    {
        "food_name": "Nutella",
        "barcode": "3017624010701",
        "ingredients": [],
    }
    {
        "food_name": "Coca-Cola Original",
        "barcode": "5449000000996",
        "ingredients": [],
    },
    {
        "food_name": "Philadelphia Original",
        "barcode": "7622300441937",
        "ingredients": [],
    },
    {
        "food_name": "Heinz Beanz in Tomato Sauce",
        "barcode": "5000157024671",
        "ingredients": [],
    },
    {
        "food_name": "Lotus Biscoff",
        "barcode": "5410126716016",
        "ingredients": [],
    },
    {
        "food_name": "Ritter Sport Marzipan Chocolate",
        "barcode": "4000417025005",
        "ingredients": [],
    },
]

SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["complete", "needs_follow_up"]},
        "potential_concern": {"type": "boolean"},
        "reason": {"type": "string"},
        "information_needed": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "potential_concern", "reason", "information_needed"],
    "additionalProperties": False,
}
EXPECTED_KEYS = set(SCHEMA["properties"])


# ---------- Storage: {username: [{"role", "text", "time"}, ...]} ----------

def load_chats():
    if not os.path.exists(CHATS_FILE):
        return {}
    with open(CHATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_chats(all_chats):
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chats, f, indent=2)


def load_decrypted_api_key(key_path="secret.key", encrypted_key_path="encrypted_api_key.bin"):
    with open(key_path, "rb") as f:
        key = f.read()
    with open(encrypted_key_path, "rb") as f:
        encrypted_key = f.read()
    return Fernet(key).decrypt(encrypted_key).decode()


# ---------- Prompts ----------

def build_system_instruction(profile):
    bmi = round(profile["weight"] / ((profile["height"] / 100) ** 2), 1)
    if "medical_conditions" not in profile:
        conditions = "not provided (unknown, NOT confirmed as none)"
    else:
        conditions = ", ".join(profile["medical_conditions"]) or "none reported"
    return (
        "You analyse food products for possible health concerns. Do not make a medical "
        "diagnosis. Return structured output only.\n\n"
        "User profile:\n"
        f"- Age: {profile['age']}\n"
        f"- Gender: {profile['gender']}\n"
        f"- Ethnicity: {profile['race']}\n"
        f"- Country: {profile['country']}\n"
        f"- Height: {profile['height']} cm\n"
        f"- Weight: {profile['weight']} kg\n"
        f"- BMI: {bmi}\n"
        f"- Medical conditions: {conditions}\n\n"
        "Tailor each assessment to this profile and to everything earlier in this "
        "conversation (previous foods and any information the user gave). If you need more "
        "information about the user, set status to 'needs_follow_up' and list each piece of "
        "information in information_needed; the user will reply with a JSON object where "
        "each key is one of your requests, filled in. Otherwise set status to 'complete' and "
        "leave information_needed empty."
    )


#def build_food_prompt(food):
    #return (f"Give a risk assessment for this food: {food['food_name']}\n"
            #f"Ingredients: {', '.join(food['ingredients'])}")


def build_follow_up_reply(requests):
    """No user input: every request is answered with 'unknown'."""
    return json.dumps({r: "unknown" for r in requests})


# ---------- Gemini session ----------

def resume_chat(client, profile, history):
    """Rebuild the user's AI chat session from saved history + profile."""
    past = [types.Content(role=m["role"], parts=[types.Part(text=m["text"])]) for m in history]
    return client.chats.create(
        model=MODEL_NAME,
        history=past,
        config={
            "system_instruction": build_system_instruction(profile),
            "response_mime_type": "application/json",
            "response_json_schema": SCHEMA,
        },
    )


def validate_response(data):
    if not isinstance(data, dict) or set(data) != EXPECTED_KEYS:
        return False
    return (
        data["status"] in ("complete", "needs_follow_up")
        and isinstance(data["potential_concern"], bool)
        and isinstance(data["reason"], str)
        and isinstance(data["information_needed"], list)
        and all(isinstance(i, str) for i in data["information_needed"])
    )


def send_message(chat, history, message):
    response = chat.send_message(message)
    text = (response.text or "").strip()
    now = int(time.time())
    history.append({"role": "user", "text": message, "time": now})
    history.append({"role": "model", "text": text, "time": now})
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def send_validated(chat, history, message, max_retries=2):
    for _ in range(max_retries + 1):
        data = send_message(chat, history, message)
        if validate_response(data):
            return data
        message = ("Your last response did not match the required schema. Resend it with "
                   "exactly these keys: " + ", ".join(sorted(EXPECTED_KEYS)))
    return None


def assess_food(chat, history, food, max_follow_ups=3):
    reply = send_validated(chat, history, build_food_prompt(food))
    rounds = 0
    while reply and reply["status"] == "needs_follow_up" and rounds < max_follow_ups:
        reply = send_validated(chat, history, build_follow_up_reply(reply["information_needed"]))
        rounds += 1
    return reply


# ---------- Menu actions ----------

def count_foods(history):
    return sum(1 for m in history if m["role"] == "user" and "risk assessment" in m["text"])


def new_chat(client, all_chats, profile):
    """Continue the user's existing AI session (history + profile) with the next test food."""
    history = all_chats[profile["username"]]
    chat = resume_chat(client, profile, history)

    food = TEST_FOODS[count_foods(history) % len(TEST_FOODS)]
    print(f"\nChecking: {food['food_name']}")
    result = assess_food(chat, history, food)

    if result:
        print(f"Potential concern: {'YES' if result['potential_concern'] else 'no'}")
        print(f"Reason: {result['reason']}")
    else:
        print("No valid response.")
    save_chats(all_chats)


def view_past_chats(all_chats, profile):
    history = all_chats[profile["username"]]
    if not history:
        print("\nNo past chats yet.")
        return
    print(f"\n--- All chats for {profile['username']} ---")
    for m in history:
        when = time.strftime("%d %b %Y %H:%M", time.localtime(m.get("time", 0)))
        if m["role"] == "user":
            print(f"\n[{when}] You: {m['text'].splitlines()[0]}")
        else:
            try:
                data = json.loads(m["text"])
                print(f"   AI ({'concern' if data['potential_concern'] else 'no concern'}): {data['reason']}")
            except (json.JSONDecodeError, KeyError):
                print("   AI: (unreadable response)")


def main():
    profiles = load_profiles()
    username = choose_username(profiles)
    profile = profiles[username]
    all_chats = load_chats()
    all_chats.setdefault(username, [])
    client = genai.Client(api_key=load_decrypted_api_key())

    try:
        while True:
            print(f"\nUser: {username}\n1. New chat\n2. Past chats\n3. Quit")
            choice = input("Choose: ").strip()
            if choice == "1":
                new_chat(client, all_chats, profile)
            elif choice == "2":
                view_past_chats(all_chats, profile)
            elif choice == "3":
                break
    finally:
        client.close()


if __name__ == "__main__":
    main()