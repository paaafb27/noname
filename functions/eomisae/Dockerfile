FROM public.ecr.aws/lambda/python:3.11

# 시스템 도구 설치
RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver-linux64.zip" "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip" && \
    curl -Lo "/tmp/chrome-linux64.zip" "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chrome-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
    unzip /tmp/chrome-linux64.zip -d /opt/ && \
RUN chmod +x /opt/chromedriver-linux64/chromedriver && \
    chmod +x /opt/chrome-linux64/chrome && \
    ln -s /opt/chromedriver-linux64/chromedriver /opt/chromedriver && \
    ln -s /opt/chrome-linux64/chrome /opt/chrome/chrome && \
    mkdir -p /opt/chrome
RUN yum install -y atk cups-libs gtk3 libXcomposite alsa-lib libXcursor libXdamage libXext libXi libXrandr libXScrnSaver libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm

# 빌드 컨텍스트의 루트부터의 전체 경로를 사용하여 파일 복사
COPY functions/eomisae/requirements.txt .
RUN pip install -r requirements.txt --target "/var/task"

# 빌드 컨텍스트의 루트부터의 전체 경로를 사용하여 소스 코드 복사
COPY functions/eomisae/lambda_function.py /var/task/
COPY functions/eomisae/scraper.py /var/task/
COPY common /var/task/common

# Lambda가 실행할 핸들러 지정
CMD [ "lambda_function.lambda_handler" ]