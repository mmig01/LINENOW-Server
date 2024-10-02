FROM python:3.12-slim

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config

    # certbot으로 SSL 인증서 발급
    apt-get install python3-certbot-nginx
    certbot certonly --nginx -d linenow.xyz

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 패키지 설치
COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# 프로젝트 전체 복사
COPY . /app

# makemigrations, migrate 실행 후 Gunicorn 시작
CMD ["sh", "-c", "python manage.py makemigrations --noinput && python manage.py migrate --noinput && gunicorn linenow.wsgi:application --bind 0.0.0.0:8000"]
