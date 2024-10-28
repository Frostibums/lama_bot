FROM python:3.10

RUN mkdir /lama_bot_app

WORKDIR /lama_bot_app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .