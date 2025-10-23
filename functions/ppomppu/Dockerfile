FROM public.ecr.aws/lambda/python:3.11

# Chrome 및 Chromedriver 설치
RUN yum install -y unzip curl
RUN curl -Lo /tmp/chrome.zip "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chrome-linux64.zip" && unzip /tmp/chrome.zip -d /opt/
RUN curl -Lo /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip" && unzip /tmp/chromedriver.zip -d /opt/
RUN chmod +x /opt/chrome-linux64/chrome /opt/chromedriver-linux64/chromedriver

# 그래픽 라이브러리 설치
RUN yum install -y atk cups-libs gtk3 libXcomposite alsa-lib libXcursor libXdamage libXext libXi libXrandr libXScrnSaver libXtst pango at-spi2-atk libXt xorg-x-server-Xvfb xorg-x11-xauth dbus-glib nss mesa-libgbm

# Python 라이브러리 설치
COPY functions/ppomppu/requirements.txt .
RUN pip install -r requirements.txt --target "/var/task"

# 소스 코드 복사
COPY functions/ppomppu/lambda_function.py /var/task/
COPY functions/ppomppu/scraper.py /var/task/
COPY common /var/task/common

# 핸들러 지정
CMD ["lambda_function.lambda_handler"]