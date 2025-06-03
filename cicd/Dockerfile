# 1. Chọn base image
FROM python:3.9-slim-bookworm

# 2. Thiết timezone
ENV TZ=Asia/Ho_Chi_Minh
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
  && echo $TZ > /etc/timezone

# 3. Cài tool hệ thống
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential gcc libpq-dev libssl-dev libffi-dev curl ca-certificates \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY . /ocr_manager
WORKDIR /ocr_manager

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

WORKDIR /ocr_manager/app
EXPOSE 9000
CMD ["python", "main.py", "/ocr_manager/.env"]
