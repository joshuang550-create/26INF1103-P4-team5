FROM python:3.14-slim

WORKDIR /smartbite

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole project (app code, lookup files, tests...).
# .dockerignore keeps secrets, git history and local data out of the image.
COPY . .

ENV USER_PROFILES="/smartbite/data/user_profiles.json" \
    CHATS="/smartbite/data/chats.json" \
    ALLERGENS="/smartbite/lookup/allergens.json" \
    THRESHOLDS="/smartbite/lookup/thresholds.json" \
    COUNTRIES="/smartbite/lookup/countries.csv" \
    ETHNICITIES="/smartbite/lookup/ethnicities.csv" \
    CONDITIONS="/smartbite/lookup/conditions.csv" \
    ENCRYPTED_API_KEY="/smartbite/encrypted_api_key.bin"

RUN mkdir -p /smartbite/data

# Default: run the application.
# To run the tests instead:
#   docker run --rm <image> python -m unittest discover -s tests -t . -v
CMD ["python", "main.py"]
