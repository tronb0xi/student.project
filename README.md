# Educational Center Management System

## Опис
Система управління освітнім центром з підтримкою філій, вчителів, студентів, груп та розкладу уроків.

## Технології
- Backend: Django + Django REST Framework
- Database: PostgreSQL
- Authentication: JWT
- Containerization: Docker Compose
- API Documentation: Swagger/OpenAPI

## Запуск проекту

### Через Docker (рекомендовано)
```bash
docker-compose up --build
```

### Локально
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

## Створення суперюзера
```bash

docker-compose exec backend python manage.py createsuperuser

python3 manage.py createsuperuser
```

## Запуск тестів
```bash
python3 manage.py test backend.core
```

## Змінні середовища
DATABASE_URL=postgresql://eduuser:edupassword@db:5432/edudb
POSTGRES_DB=edudb
POSTGRES_USER=eduuser
POSTGRES_PASSWORD=edupassword
DEBUG=True

## API документація

Swagger локально:
http://127.0.0.1:8000/api/docs/

Swagger на Render:
https://student-project-cv8v.onrender.com/api/docs/

## Ролі користувачів
- **ADMIN** — повний доступ: управління студентами, вчителями, розкладом, звітами
- **TEACHER** — перегляд свого розкладу, відмітка відвідуваності

## Тестові акаунти
### Адміністратор
Номер телефону: +380000000001  
Пароль: 111

### Викладач
Номер телефону: +380000000002  
Пароль: 111

### Викладач 2
Номер телефону: +380000000003  
Пароль: 111