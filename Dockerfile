FROM python:3.12-slim

WORKDIR /app

# 의존성 먼저 설치 (코드만 바뀌었을 때 캐시 재사용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app2.py"]
