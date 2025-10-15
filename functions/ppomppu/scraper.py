"""
뽐뿌 크롤러

URL: https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu
필터링: 공지, 쇼핑뽐뿌, 핫딜, 쇼핑포럼 제외
판매처: <em class="subject_preface"> 또는 제목에서 추출
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import sys
import os
import re

# common 모듈
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.time_filter import filter_by_time
from common.price_extractor import extract_price_from_title

class PpomppuScraper:

    def __init__(self):
        self.url = 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
        self.source_site = 'PPOMPPU'
        self.main_url = 'https://www.ppomppu.co.kr/zboard/'

    def scrape(self):
        """페이징 크롤링 (30분 필터링)"""
        return self._scrape_with_pagination()

    def _scrape_with_pagination(self):

        all_items = []

        # 1페이지 크롤링
        print("1페이지 크롤링 중...")
        page1_items = self._scrape_page(1)

        if not page1_items:
            return []

        page1_filtered = filter_by_time(page1_items, minutes=30)
        all_items.extend(page1_filtered)
        print(f"1페이지: {len(page1_items)}개 → 필터링 {len(page1_filtered)}개")

        # 2페이지 확인 조건
        if len(page1_items) > 0:
            from datetime import datetime, timedelta
            from time_filter import parse_time

            last_item = page1_items[-1]
            last_time = parse_time(last_item.get('crawledAt', ''))

            if last_time:
                cutoff_time = datetime.now() - timedelta(minutes=30)

                # 마지막 게시글이 30분 이내면 2페이지 확인
                if (last_time >= cutoff_time):
                    print("2페이지 확인")
                    page2_items = self._scrape_page(2)

                    if page2_items:
                        page2_filtered = filter_by_time(page2_items, minutes=30)
                        all_items.extend(page1_filtered)
                        print(f"2페이지: {len(page2_items)}개 → 필터링 {len(page2_filtered)}개")

    def _scrape_page(self, page_num):
        """
        개별 페이지 크롤링
        """

        items = []

        with sync_playwright() as p:
            # 브라우저 실행
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            page = browser.new_page()

            # image/css 차단 for 속도 향상
            page.route(
                "**/*.{png,jpg,jpeg,gif,svg,webp,css,woff,woff2}",
                lambda route: route.abort()
            )

            try:
                if page_num == 1:
                    url = self.url
                else:
                    url = f"{self.url}&page={page_num}"

                # 페이지 로딩
                page.goto(
                    url,
                    timeout=30000,
                    wait_until='domcontentloaded'
                )
                # 테이블 로딩 대기
                page.wait_for_selector('#revolution_main_table', timeout=10000)

                # HTML 파싱
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 게시글 목록
                rows = soup.select('#revolution_main_table tbody tr.baseList.bbs_new1')
                print(f"페이지 {page_num}: {len(rows)}개 발견")

                for row in rows:
                    try:
                        # 필터링 : 공지 / 광고 제외
                        if self._is_excluded(row):
                            continue

                        # 데이터 추출
                        item = self._extract_item(row)
                        if item:
                            items.append(item)

                    except Exception as e:
                        print(f"게시글 파싱 실패: {e}")
                        continue

            finally:
                browser.close()
    def _is_excluded(self, row):
        """
        제외 조건:
        - 글번호 영역에 <img> 태그 포함 (쇼핑뽐뿌, 핫딜, 쇼핑포럼)
        """
        # img
        numb_cell = row.select_one('td.baseList-space.baseList-numb')
        if numb_cell and numb_cell.find('img'):
            return True

        return False

    def _extract_items(self, row):
        """
        세일정보 추출
        """
        # 제목
        title_element = row.select_one('a.baseList-title')
        if not title_element:
            return None
        title = title_element.get_text(strip=True)

        # URL
        product_url = self.main_url + title_element['href']

        # 판매처
        # 1) element 확인
        # 2) 제목에서 [판매처] 추출
        store_element = title_element.select_one('em.baseList-head.subject_preface')
        if store_element:
            store = store_element.get_text(strip=True)
        else: '기타'

        # 가격
        price = extract_price_from_title(title)

        # 배송비
        #shipping_fee_element = row.select_one('span.deal-delivery')
        #shipping_fee = shipping_fee_element.get_text(strip=True) if store_element else ''

        # 등록 시간
        time_element = row.select_one('time.baseList-time')
        time = time_element.get_text(strip=True) if time_element else ''

        # 댓글 수
        reply_element = title_element.select_one('span.baseList-c')
        reply_count = reply_element.get_text(strip=True) if reply_element else None

        # 좋아요 수
        like_element = row.title_element('td.baseList-rec')
        like_count = like_element.get_text(strip=True) if like_element else None

        # 이미지 url
        image_element = row.select_one('a.baseList-thumb')
        image_url = self.main_url + image_element['href']

        return {
            'title': title,
            'price': price,
            'storeName': store,
            #'shippingFee': shipping_fee,
            'productUrl': product_url,
            'imageUrl': image_url,
            'replyCount': reply_count,
            'likeCount': like_count,
            'sourceSite': self.source_site,
            'crawledAt': time
        }

