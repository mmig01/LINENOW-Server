FROM python:3.12-slim

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 종속성 설치
COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# .env 파일 복사
COPY .env /app/.env

# Docker 빌드 시 환경 변수 받기
ARG SECRET_KEY
ARG DEBUG
ARG DJANGO_DEPLOY

# 환경 변수를 컨테이너 내에서 사용할 수 있게 설정
ENV SECRET_KEY=$SECRET_KEY
ENV DEBUG=$DEBUG
ENV DJANGO_DEPLOY=$DJANGO_DEPLOY

# 프로젝트 파일 복사
COPY . /app

# collectstatic 명령 실행
RUN python manage.py collectstatic --noinput

# Gunicorn으로 Django 애플리케이션 실행
CMD ["gunicorn", "linenow.wsgi:application", "--bind", "0.0.0.0:8000"]