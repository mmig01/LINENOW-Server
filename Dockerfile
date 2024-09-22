FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# Docker 빌드 시 환경 변수 받기
ARG SECRET_KEY
ARG DEBUG
ARG DJANGO_DEPLOY

# 환경 변수를 컨테이너 내에서 사용할 수 있게 설정
ENV SECRET_KEY=$SECRET_KEY
ENV DEBUG=$DEBUG
ENV DJANGO_DEPLOY=$DJANGO_DEPLOY

COPY . /app

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "linenow.wsgi:application", "--bind", "0.0.0.0:8000"]