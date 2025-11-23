FROM python:3.12-slim

WORKDIR /app

# 裝我們需要的套件
RUN pip install --no-cache-dir fastapi uvicorn pydantic pymysql cryptography

COPY app.py /app/app.py

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
