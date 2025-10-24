# 1. 기반 이미지를 표준 Python 이미지로 변경
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /usr/src/app

# 필요한 라이브러리 설치 (Debian 방식)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        unzip \
        curl \
        libatk1.0-0 \
        libcairo2 \
        libcups2 \
        libgtk-3-0 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxi6 \
        libxrandr2 \
        libxss1 \
        libxtst6 \
        libpango-1.0-0 \
        libnss3 \
        libgbm-dev \
        dbus-x11 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chrome 및 Chromedriver 설치 (경로 동일)
# RUN curl -Lo /tmp/chrome.zip "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chrome-linux64.zip" && unzip /tmp/chrome.zip -d /opt/
# RUN curl -Lo /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip" && unzip /tmp/chromedriver.zip -d /opt/
# RUN chmod +x /opt/chrome-linux64/chrome /opt/chromedriver-linux64/chromedriver

# 3. Python 라이브러리 설치
COPY functions/fmkorea/requirements.txt .
RUN pip install -r requirements.txt

# 4. 소스 코드 복사
COPY functions/fmkorea/lambda_function.py .
COPY functions/fmkorea/scraper.py .
COPY common ./common

# 5. ECS Fargate용 진입점 지정 (수정됨)
# scraper.py가 아닌 lambda_function.py를 실행
CMD ["python", "lambda_function.py"]