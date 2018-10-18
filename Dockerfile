FROM python:3.6

ENV GROUP_ID=''
ENV BOT_API_KEY=''
ENV MASTER_ID=''

WORKDIR /thorbot

ADD . /thorbot

RUN pip install -r requirements.txt

CMD ["python", "thorbot/thorbot.py"]
