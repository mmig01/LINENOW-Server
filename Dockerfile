# 1. Python 3.12 기반 Docker 이미지 사용
FROM python:3.12

# 2. 작업 디렉토리 설정
WORKDIR /

# 3. 빌드 시 환경 변수 전달받기
ARG SECRET_KEY
ARG DEBUG
ARG DJANGO_DEPLOY
ARG DB_ENGINE
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST
ARG DB_PORT
ARG SMS_TOKEN_KEY
ARG SMS_API_KEY
ARG SEND_PHONE
ARG SSODAA_BASE_URL
ARG REDIS_HOST
ARG PGBOUNCER_HOST
ARG PGBOUNCER_PORT
# ★ 3-1. 런타임 바인딩 포트 (기본 8000)
ARG PORT=8000
ENV PORT=${PORT}
# 동시 접속을 처리할 워커 수 (필요에 따라 조정)
ARG WORKERS=4
ENV WORKERS=${WORKERS}

# 4. 환경 변수를 Docker 컨테이너 내부에 설정
ENV SECRET_KEY=${SECRET_KEY}
ENV DEBUG=${DEBUG}
ENV DJANGO_DEPLOY=${DJANGO_DEPLOY}
ENV DB_ENGINE=${DB_ENGINE}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV DB_HOST=${DB_HOST}
ENV DB_PORT=${DB_PORT}
ENV SMS_TOKEN_KEY=${SMS_TOKEN_KEY}
ENV SMS_API_KEY=${SMS_API_KEY}
ENV SEND_PHONE=${SEND_PHONE}
ENV SSODAA_BASE_URL=${SSODAA_BASE_URL}
ENV REDIS_HOST=${REDIS_HOST}
# Celery broker configuration
ENV CELERY_BROKER_URL=redis://${REDIS_HOST}:6379/0
ENV CELERY_RESULT_BACKEND=${CELERY_BROKER_URL}
ENV PGBOUNCER_HOST=${PGBOUNCER_HOST}
ENV PGBOUNCER_PORT=${PGBOUNCER_PORT}

# 5. 로컬의 Django 프로젝트 파일을 컨테이너 내부로 복사
COPY . /

# 6. 패키지 설치
RUN pip install --upgrade pip && pip install -r requirements.txt
# ASGI 최적화용 서버 및 라이브러리 설치
RUN pip install gunicorn uvicorn uvloop httptools

CMD ["sh", "-c", "ulimit -n 10000 && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn linenow.asgi:application -k uvicorn.workers.UvicornWorker -w ${WORKERS} --bind 0.0.0.0:${PORT} --backlog 2048"]