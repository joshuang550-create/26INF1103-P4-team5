FROM python:3.14-slim

WORKDIR /smartbite

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY logic_test.py .
COPY encrypted_api_key.bin .

COPY managers/io_manager.py ./managers/
COPY managers/ai_manager.py ./managers/
COPY managers/logic_manager.py ./managers/
COPY managers/data_manager.py ./managers/

COPY lookup/allergens.json ./lookup/
COPY lookup/thresholds.json ./lookup/
COPY lookup/countries.csv ./lookup/
COPY lookup/ethnicities.csv ./lookup/

ENV USER_PROFILES="/smartbite/data/user_profiles.json"
ENV CHATS="/smartbite/data/chats.json"
ENV ALLERGENS="/smartbite/lookup/allergens.json"
ENV THRESHOLDS="/smartbite/lookup/thresholds.json"
ENV COUNTRIES="/smartbite/lookup/countries.csv"
ENV ETHNICITIES="/smartbite/lookup/ethnicities.csv"
ENV ENCRYPTED_API_KEY="/smartbite/encrypted_api_key.bin"

RUN mkdir -p /smartbite/data

CMD ["python", "main.py"]
