# 1. Python 3.13 기반 Docker 이미지 사용
FROM python:3.13

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


# 5. 로컬의 Django 프로젝트 파일을 컨테이너 내부로 복사
COPY . /

# 6. 패키지 설치
RUN pip install --upgrade pip && pip install -r requirements.txt

# 7. Django 정적 파일 수집 및 마이그레이션 (빌드 시)
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

# 8. Gunicorn 실행 (Django 서버 실행)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "linenow.wsgi:application"]