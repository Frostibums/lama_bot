FROM python:3.10

RUN mkdir /cryptorelax_bot_app

WORKDIR /cryptorelax_bot_app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .