FROM tiangolo/uvicorn-gunicorn:python3.8-slim

COPY . /usr/src/app
COPY requirements.txt .

RUN pip install pika;
RUN pip3 install -r requirements.txt

EXPOSE 8000

WORKDIR /usr/src/app