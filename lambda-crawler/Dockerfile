# AWS Lambda Python 3.11 기본 이미지
FROM public.ecr.aws/lambda/python:3.11

# Chrome과 ChromeDriver 다운로드 및 설치
# 사용 의도: Lambda 환경에서 Selenium + Chrome 실행
# 효과: 동적 크롤링 가능, 검증된 방법
RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver-linux64.zip" "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip" && \
    curl -Lo "/tmp/chrome-linux64.zip" "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chrome-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
    unzip /tmp/chrome-linux64.zip -d /opt/ && \
    chmod +x /opt/chromedriver-linux64/chromedriver && \
    chmod +x /opt/chrome-linux64/chrome && \
    rm /tmp/chromedriver-linux64.zip /tmp/chrome-linux64.zip

# 필요한 라이브러리 설치 (Chrome 실행용)
# 사용 의도: Chrome 실행에 필요한 시스템 라이브러리
RUN yum install -y \
    atk \
    cups-libs \
    gtk3 \
    libXcomposite \
    alsa-lib \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXScrnSaver \
    libXtst \
    pango \
    at-spi2-atk \
    libXt \
    xorg-x11-server-Xvfb \
    xorg-x11-xauth \
    dbus-glib \
    dbus-glib-devel \
    nss \
    mesa-libgbm

# Python 패키지 설치
RUN pip install selenium==4.15.2 beautifulsoup4==4.12.2 lxml==4.9.3 requests==2.31.0

# Lambda 함수 코드
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.lambda_handler" ]