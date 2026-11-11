FROM python:3.14-slim

WORKDIR /smartbite

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py encrypted_api_key.bin ./
COPY app/ ./app/
COPY managers/ ./managers/
COPY models/ ./models/
COPY prompts/ ./prompts/
COPY lookup/ ./lookup/
COPY tests/ ./tests/

ENV USER_PROFILES="/smartbite/data/user_profiles.json" \
    CHATS="/smartbite/data/chats.json" \
    ALLERGENS="/smartbite/lookup/allergens.json" \
    THRESHOLDS="/smartbite/lookup/thresholds.json" \
    COUNTRIES="/smartbite/lookup/countries.csv" \
    ETHNICITIES="/smartbite/lookup/ethnicities.csv" \
    CONDITIONS="/smartbite/lookup/conditions.csv" \
    ENCRYPTED_API_KEY="/smartbite/encrypted_api_key.bin"

RUN mkdir -p /smartbite/data

# Default: run the application.  To run the tests instead, see TESTING.md.
CMD ["python", "main.py"]
