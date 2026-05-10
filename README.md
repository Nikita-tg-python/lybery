# 📚 Library API & User Management System

Современный и безопасный RESTful API для управления библиотекой и ролями пользователей. Проект демонстрирует реализацию надежной архитектуры бэкенда с использованием **FastAPI** и **PostgreSQL**.

## 🚀 Ключевые возможности (Features)

* **Продвинутая аутентификация:** Реализован безопасный вход и регистрация с использованием **JWT-токенов** (JSON Web Tokens).
* **Role-Based Access Control (RBAC):** Разделение прав доступа на уровне ролей:
  * `User` — базовые права.
  * `Librarian` — права на управление библиотечным фондом и данными пользователей.
  * `SuperUser` — полный административный доступ.
* **Безопасность данных:** Надежное хеширование паролей (pwdlib/passlib) и защита эндпоинтов.
* **ORM & Валидация:** Строгая типизация и работа с базой данных через **SQLModel**

## 🛠 Технологический стек

* **Язык:** Python 3.10+
* **Фреймворк:** FastAPI
* **База данных:** PostgreSQL
* **ORM:** SQLModel
* **Аутентификация:** PyJWT, OAuth2 (Password Bearer)
* **Сервер:** Uvicorn

## ⚙️ Локальный запуск проекта

### 1. Клонирование репозитория
```bash
git clone https://github.com/Nikita-tg-python/lybery.git
cd lybery
```
### 2. Настройка виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Для Linux/macOS
# venv\Scripts\activate   # Для Windows
```
### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```
### 4. Настройка переменных окружения

Секретный ключ для подписи JWT токенов (сгенерируйте надежный ключ)
Для этого используйте команду:
```bash 
openssl rand -hex 32
```

Создайте файл .env в корневой папке проекта и добавьте следующие настройки:

```bash
KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Настройка базы данных

Убедитесь, что у вас установлен и запущен локальный сервер PostgreSQL. Создайте базу данных (например, book_db) и обновите строку подключения sql_url в файле с настройками базы данных:
```bash
postgresql://<username>:<password>@localhost:5432/book_db
```

### 6. Запуск сервера
```bash
fastapi dev main.py
```
## 📖 Документация API (Swagger UI)

FastAPI автоматически генерирует интерактивную документацию. После запуска сервера она будет доступна по адресам:
* **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🗄 Структура основных API Эндпоинтов

### Аутентификация
* `POST /register` — Регистрация нового пользователя
* `POST /login` — Получение JWT access-токена

### Управление пользователями
* `GET /get/user` — Получение данных текущего авторизованного пользователя
* `PATCH /user/password/{username}` — Безопасная смена пароля
* `PATCH /users/{username}` — Обновление данных пользователя (доступно для `Librarian`)
* `PATCH /admin/librarians/{username}` — Выдача прав библиотекаря (доступно только для `SuperUser`)

---
**👤 Автор:** Никита (Python Backend Developer)
* [GitHub](https://github.com/Nikita-tg-python)
* [Telegram](https://t.me/Necro_fus)