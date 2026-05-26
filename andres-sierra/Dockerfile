FROM python:3.11-slim

WORKDIR /app

COPY codigo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY codigo/ ./codigo/

ENV FLASK_PORT=8080
EXPOSE 8080

CMD ["python", "codigo/app.py"]
