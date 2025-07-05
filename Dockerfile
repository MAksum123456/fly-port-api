FROM python:3.12-alpine3.18
LABEL maintainer="smolinskijmaksim1@gmail.com"

ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
