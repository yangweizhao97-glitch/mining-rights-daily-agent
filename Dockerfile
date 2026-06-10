FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUTF8=1
ENV PYTHONPATH=/app

CMD ["python", "agent/main.py", "给我生成一份关于 Pilbara 锂矿的今日简报"]

