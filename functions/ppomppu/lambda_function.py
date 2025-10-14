"""
크롤러 Lambda 함수

연동: Spring Boot CrawlDataController
"""

import json
import os
import time
import re
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# 환경 변수
API_URL = os.environ.get('API_URL')  # Spring Boot API
API_KEY = os.environ.get('API_KEY')  # 인증 키
SITE_NAME = 'PPOMPPU'              # SourceSite enum 값

######################################################################

def lambda_handler(event, context):
    """
    Lambda 핸들러

    EventBridge가 10분마다 호출
    """
    start_time = time.time()

    try:
        print(f"[{SITE_NAME}] 크롤링 시작 ...")

        items = crawl_ppomppu()

        print(f"[{SITE_NAME}] 크롤링 완료: {len(items)}개")

        result = send_to_api(items)

        execution_time = time.time() - start_time

        return {
            'statusCode': 200,
            'body': json.dumps({
                'site': SITE_NAME,
                'total_items': len(items),
                'execution_time': f"{execution_time:.2f}s",
                'api_status': 'success' if result else 'failed'
            }, ensure_ascii=False) # 한글 깨짐 방지
        }

    except Exception as e:
        print(f"[{SITE_NAME}] 에러: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'site': SITE_NAME, 'error': str(e)})
        }

def crawl_ppomppu():
    items = []
    cutoff_time = datetime.now() - timedelta(minutes=20)  # 20분 전

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process'
            ]
        )

        page = browser.new_page()

        # 이미지/css 차단 for 속도 향상
        page.route(
            "**/*.{png, jpg, jpeg, gif, svg, webp, css, woff, woff2}",
            lambda route: route.abort()
        )

        try:
            url = 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu'

            print(f"[{SITE_NAME}] 페이지 로딩: {url}")

            page.goto(url, timeout=15000, wait_until='documentloaded')

            html = page.content()
            soup = BeautifulSoup(html, 'lxml')

            articles = soup.select('tr[class*="list"]')[:50]
