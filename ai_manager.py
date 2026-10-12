"""Food risk analysis with a persistent Gemini chat session per user.
Only input: menu choice. Foods are hard-coded test data."""
import json
import os
import time
from cryptography.fernet import Fernet
from google import genai
from google.genai import types
import logging
from ai_manager_error_handling import send_validated
from openfoodfacts_prompt import (
    build_food_prompt,
    SCHEMA,
    EXPECTED_KEYS,
    validate_response,
)

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
    history = all_chats[profile["username"]]
    chat = resume_chat(client, profile, history)

    food = TEST_FOODS[count_foods(history) % len(TEST_FOODS)]
    print(f"\nChecking: {food['food_name']}")

    result = assess_food(chat, history, food)

    if result is None:
        print("No valid response.")
    else:
        if result["status"] == "needs_follow_up":
            print("Assessment incomplete - more information is needed.")

        # Display the full JSON, including the confidence score.
        print(json.dumps(result, indent=2, ensure_ascii=False))

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
    client = genai.Client(
    api_key=load_decrypted_api_key(),
    http_options=types.HttpOptions(
        timeout=30000,  # 30 seconds, specified in milliseconds
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)
    logging.basicConfig(
     filename="ai_manager_errors.log",
     level=logging.WARNING,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
     encoding="utf-8",

 )

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