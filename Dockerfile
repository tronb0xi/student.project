FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD sh -c "python manage.py migrate && python manage.py shell -c \"from backend.users.models import User; User.objects.filter(phone_number='+380000000001').exists() or User.objects.create_superuser(phone_number='+380000000001', password='111')\" && python manage.py collectstatic --noinput && gunicorn backend.config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 30"