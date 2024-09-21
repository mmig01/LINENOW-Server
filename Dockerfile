FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

COPY . /app

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "your_project_name.wsgi:application", "--bind", "0.0.0.0:8000"]