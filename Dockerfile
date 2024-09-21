FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

COPY . /app

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "linenow.wsgi:application", "--bind", "0.0.0.0:8000"]