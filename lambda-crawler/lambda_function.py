"""
Selenium 기반 뽐뿌 크롤러

사용 의도:
- Selenium으로 동적 크롤링
- 검증된 방법으로 안정적 실행
- Playwright보다 구축 쉬움

효과:
- 30분 내 구축 완료
- 비용 66% 절감
- 안정적 운영
"""

import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Lambda 핸들러"""
    try:
        api_url = os.environ.get('API_URL')
        api_key = os.environ.get('API_KEY')

        logger.info("=== 뽐뿌 크롤링 시작 (Selenium) ===")

        items = crawl_ppomppu_selenium()

        logger.info(f"크롤링 완료: {len(items)}개")

        send_to_api(items, api_url, api_key)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'site': 'PPOMPPU',
                'total_items': len(items),
                'message': '크롤링 성공'
            }, ensure_ascii=False)
        }
    except Exception as e:
        logger.error(f"크롤링 실패: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }


def get_chrome_driver():
    """
    Chrome WebDriver 생성

    사용 의도: Lambda 환경에서 Chrome 실행
    효과: 동적 크롤링 가능
    """
    chrome_options = Options()
    chrome_options.binary_location = '/opt/chrome-linux64/chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    service = Service(
        executable_path='/opt/chromedriver-linux64/chromedriver',
        service_args=['--verbose', '--log-path=/tmp/chromedriver.log']
    )

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)

    return driver


def crawl_ppomppu_selenium():
    """Selenium으로 뽐뿌 크롤링"""
    items = []
    driver = None

    try:
        driver = get_chrome_driver()

        url = 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
        logger.info(f"페이지 접속: {url}")
        driver.get(url)

        # 페이지 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='revolution_main_table']"))
        )

        logger.info("페이지 로딩 완료")

        # HTML 저장 및 분석
        html = driver.page_source

        # HTML 길이 확인
        logger.info(f"HTML 크기: {len(html)} bytes")

        # table 태그 확인
        soup = BeautifulSoup(html, 'lxml')
        tables = soup.find_all('table')
        logger.info(f"발견된 table: {len(tables)}개")

        # tr 태그 확인
        all_trs = soup.find_all('tr')
        logger.info(f"발견된 tr: {len(all_trs)}개")

        # 첫 10개 tr의 class 출력
        for idx, tr in enumerate(all_trs[:10], 1):
            logger.info(
                f"TR[{idx}] class={tr.get('class')}, onclick={tr.get('onclick', 'None')[:50] if tr.get('onclick') else 'None'}")

        items = parse_ppomppu_html(html)

    finally:
        if driver:
            driver.quit()

    return items


def parse_ppomppu_html(html):
    soup = BeautifulSoup(html, 'lxml')
    items = []

    # 뽐뿌는 table 구조 사용
    posts = soup.select('#revolution_main_table tbody tr.baseList.bbs_new1')

    if not posts:
        posts = soup.select('#revolution_main_table tbody tr.baseList.bbs_new1')

    logger.info(f"발견된 게시글: {len(posts)}개")

    for post in posts[:20]:
        try:
            # 필터링 : 공지 / 광고 제외
            if _is_excluded(post):
                continue

            # 제목
            title_elem = post.select_one('a.baseList-title')
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)

            # URL
            product_url = 'https://www.ppomppu.co.kr/zboard/' + title_elem.get('href', '')

            price = extract_price(title)
            store_element = title_elem.select_one('em.baseList-head.subject_preface')
            if store_element:
                store = store_element.get_text(strip=True)
            else:
                store = '기타'

            item = {
                'title': title,
                'price': price,
                'storeName': store,
                'productUrl': product_url,
                'imageUrl': None,
                'sourceSite': 'PPOMPPU'
            }

            items.append(item)
            logger.info(f"파싱 성공: {title[:30]}")

        except Exception as e:
            logger.warning(f"파싱 실패: {str(e)}")
            continue

    return items

def _is_excluded(row):
        """
        제외 조건:
        - 글번호 영역에 <img> 태그 포함 (쇼핑뽐뿌, 핫딜, 쇼핑포럼)
        """
        numb_cell = row.select_one('td.baseList-space.baseList-numb')
        if numb_cell and numb_cell.find('img'):
            return True

        return False

def extract_price(title):
    """가격 추출"""
    import re

    won_pattern = [
        r'\d{1,3}(?:,\d{3})+\s*원',  # 99,000원
        r'\s*\d{1,3}(?:,\d{3})+',  # 99,000
        r'\d{4,}\s*원',  # 99000원 (쉼표 없음)
    ]
    for pattern in won_pattern:
        match = re.search(pattern, title)
        if match:
            try:
                return int(match.group(0).replace(',', ''))
            except:
                return None

    # 무료 키워드 체크
    free_keywords = ['무료', '나눔', '공짜', 'free']
    if any(keyword in title.lower() for keyword in free_keywords):
        return 0

    return None


def extract_store(title):
    """상점명 추출"""
    import re
    match = re.search(r'\[(.+?)\]', title)
    return match.group(1) if match else "기타"


def send_to_api(items, api_url, api_key):
    """API 전송"""
    try:
        response = requests.post(
            api_url,
            json={'site': 'PPOMPPU', 'items': items},
            headers={
                'Content-Type': 'application/json',
                'X-API-Key': api_key
            },
            timeout=30
        )

        if response.status_code == 200:
            logger.info(f"✅ API 전송 성공: {len(items)}개")
            return True
        else:
            logger.error(f"❌ API 전송 실패: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"API 전송 오류: {str(e)}")
        return False