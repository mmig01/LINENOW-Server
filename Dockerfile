FROM python:3.12-slim

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 패키지 설치
COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# 프로젝트 전체 복사
COPY . /app

# .env 파일 복사
COPY .env /app/.env

# 정적 파일 수집
RUN python manage.py collectstatic --noinput

# makemigrations, migrate 실행 후 Gunicorn 시작
CMD ["sh", "-c", "python manage.py makemigrations --noinput && python manage.py migrate --noinput && gunicorn linenow.wsgi:application --bind 0.0.0.0:8000"]
