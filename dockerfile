FROM python:3.10-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN touch .env
RUN mkdir db
RUN echo "{}" > db/Translator.json
RUN echo "{}" > db/QuickResponses.json

CMD [ "python3", "./bot.py"]