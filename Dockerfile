FROM python:3.11-slim
LABEL maintainer="Connor Lund <cml1010101@gmail.com>"
LABEL description="Part Number generator"
LABEL version="1.0"

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "backend.py"]