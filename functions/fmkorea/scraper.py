"""
FMKOREA 크롤러

URL: https://www.fmkorea.com/hotdeal
"""

import sys
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from common.number_extractor import extract_number_from_text
from common.time_filter import filter_by_time, parse_time

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))


class FmkoreaScraper:

    def __init__(self):
        self.url = 'https://www.fmkorea.com/hotdeal'
        self.main_url = 'https://www.fmkorea.com'
        self.source_site = 'FMKOREA'

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

        # 1페이지 필터링
        page1_filtered = filter_by_time(page1_items, minutes=30)
        all_items.extend(page1_filtered)

        print(f"1페이지: {len(page1_items)}개 → 필터링 {len(page1_filtered)}개")

        # 2페이지 확인 조건
        if len(page1_items) > 0:
            from datetime import datetime, timedelta

            last_item = page1_items[-1]
            last_time = parse_time(last_item.get('crawledAt', ''))

            if last_time:
                cutoff_time = datetime.now() - timedelta(minutes=30)

                # 마지막 게시글이 30분 이내면 2페이지 확인
                if last_time >= cutoff_time:
                    print("→ 2페이지 확인 필요")
                    page2_items = self._scrape_page(2)

                    if page2_items:
                        page2_filtered = filter_by_time(page2_items, minutes=30)
                        all_items.extend(page2_filtered)
                        print(f"2페이지: {len(page2_items)}개 → 필터링 {len(page2_filtered)}개")
                else:
                    print("2페이지 확인 불필요 (마지막 게시글 30분 초과)")

        return all_items

    def _scrape_page(self, page_num):

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
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                ]
            )
            page = browser.new_page()

            # image/css 차단 for 속도 향상
            page.route(
                "**/*.{png,jpg,jpeg,gif,svg,webp,css,woff,woff2}",
                lambda route: route.abort()
            )

            try:
                # 페이지 URL
                if page_num == 1:
                    url = self.url
                else:
                    url = f"{self.main_url}/index.php?mid=hotdeal&page={page_num}"

                # 페이지 로딩
                page.goto(
                    url,
                    timeout=30000,
                    wait_until='domcontentloaded'
                )

                # 테이블 로딩 대기
                page.wait_for_selector('div.fm_best_widget._bd_pc', timeout=10000)

                # HTML 파싱
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 게시글 목록
                rows = soup.select('div.fm_best_widget._bd_pc li.li_best2_hotdeal0')
                print(f"게시글 {len(rows)}개 발견")

                for row in rows:
                    try:
                        # 데이터 추출
                        item = self._extract_item(row)

                        if item:
                            items.append(item)

                    except Exception as e:
                        print(f"게시글 파싱 실패: {e}")
                        continue

            finally:
                browser.close()

        return items

    def _extract_item(self, row):
        """
        세일정보 추출
        """
        # 제목
        title_element = row.select_one('span.ellipsis-target')
        if not title_element:
            return None
        title = title_element.get_text(strip=True)

        # URL
        url_element = row.select_one('div.li a.hotdeal_var8')
        product_url = self.main_url + url_element['href']

        # 판매처
        store_selector = "//div[@class='fm_best_widget _bd_pc']//li[contains(@class, 'li_best2_hotdeal0')]//span[contains(text(), '쇼핑몰')]/a[@class='strong']"
        store_element = row.locator(f"xpath={store_selector}")
        if store_element:
            store = store_element.get_text(strip=True)
        else:
            '기타'

        # 가격
        price_selector = "//div[@class='fm_best_widget _bd_pc']//li[contains(@class, 'li_best2_hotdeal0')]//span[contains(text(), '가격')]/a[@class='strong']"
        price_element = row.locator(f"xpath={price_selector}")
        price = price_element.get_text(strip=True) if price_element else ''

        # 배송비
        shipping_fee_selector = "//div[@class='fm_best_widget _bd_pc']//li[contains(@class, 'li_best2_hotdeal0')]//span[contains(text(), '배송')]/a[@class='strong']"
        shipping_fee_element = row.locator(f"xpath={shipping_fee_selector}")
        shipping_fee = shipping_fee_element.get_text(strip=True) if price_element else None

        # 등록 시간
        time_element = row.select_one('span.regdate')
        time = time_element.get_text(strip=True) if time_element else None

        # 댓글 수
        reply_element = row.select_one('span.comment_count')
        reply_count = reply_element.get_text(strip=True) if reply_element else 0

        # 추천 수
        like_elemet = row.select_one('div.fm_best_widget._bd_pc li.li_best2_hotdeal0 span.count')
        like_count = like_elemet.get_text(strip=True) if reply_element else 0

        # 이미지 url
        image_element = row.select_one('img.thumb')
        image_url = image_element['href'] if image_element else None

        return {
            'title': title,
            'price': price,
            'storeName': store,
            'shippingFee': shipping_fee,
            'productUrl': product_url,
            'imageUrl': image_url,
            'replyCount': reply_count,
            'likeCount': like_count,
            'sourceSite': self.source_site,
            'crawledAt': time
        }