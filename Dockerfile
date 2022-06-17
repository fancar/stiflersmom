FROM python:3.7

WORKDIR /app
ARG requirements=requirements/production.txt

COPY . /app

RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir -r $requirements
