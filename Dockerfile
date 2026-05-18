FROM python:3.11

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD [ "fastapi", "run", "main.py", "--port", "8000", "--host", "0.0.0.0"]