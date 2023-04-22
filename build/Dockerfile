FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED=1

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY app/ /app/

COPY build/bootstrap.sh .
RUN chmod +x bootstrap.sh

CMD ["/app/build/bootstrap.sh"]
