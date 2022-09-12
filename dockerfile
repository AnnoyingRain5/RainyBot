FROM python:3.10

WORKDIR /usr/src/

RUN git clone https://github.com/AnnoyingRain5/RainyBot app

WORKDIR /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

RUN touch .env
RUN mkdir db
RUN echo "{}" > db/Translator.json
RUN echo "{}" > db/QuickResponses.json
VOLUME ["/usr/src/app/db"]

CMD git pull; pip install --no-cache-dir -r requirements.txt; python3 ./bot.py