FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sms_engine/ sms_engine/
COPY frontend_sms/ frontend_sms/

ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

CMD exec uvicorn sms_engine.main:app --host 0.0.0.0 --port $PORT --workers 2
