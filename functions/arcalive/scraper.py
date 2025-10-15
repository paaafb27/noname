"""
ARCALIVE 크롤러

URL: https://arca.live/b/hotdeal
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import sys
import os

from common.time_filter import filter_by_time

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

class ArcaliveScraper:

    def __init__(self):
        self.url = 'https://arca.live/b/hotdeal'
        self.source_site = 'ARCALIVE'
        self.main_url = "https://arca.live"

    def scrape(self):

        items = []

        with sync_playwright() as p:
            # 브라우저 실행
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )

            page = browser.new_page()

            # image/css 차단 for 속도 향상
            page.route(
                "**/*.{png,jpg,jpeg,gif,svg,webp,css,woff,woff2}",
                lambda route: route.abort()
            )

            try:
                print(f"페이지 접속: {self.url}")

                # 페이지 로딩
                page.goto(
                    self.url,
                    timeout=30000,
                    wait_until='domcontentloaded'
                )

                # 테이블 로딩 대기
                page.wait_for_selector('div.list-table hybrid', timeout=10000)

                # HTML 파싱
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 게시글 목록
                rows = soup.select('div.list-table.hybrid div.vrow.hybrid')
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

        print(f"필터링 전: {len(items)}개")

        # 30분 기준 필터링
        filtered_items = filter_by_time(items, minutes=30)

        print(f"30분 필터링 후: {len(filtered_items)}개")

        return filtered_items

    def _extract_item(self, row):
        """
        세일정보 추출
        """
        # 제목
        title_element = row.select_one('a.title.hybrid-title')
        if not title_element:
            return None
        title = title_element.get_text(strip=True)

        # url
        url_element = row.select_one('div.vrow.hybrid a.title.preview-image')
        product_url = self.main_url + url_element['href']

        # 판매처
        store_element = row.select_one('span.deal-store')
        store = store_element.get_text(strip=True) if store_element else '기타'

        # 가격
        price_element = row.select_one('span.deal-price')
        price = price_element.get_text(strip=True) if price_element else ''

        # 배송비
        shipping_fee_element = row.select_one('span.deal-delivery')
        shipping_fee = shipping_fee_element.get_text(strip=True) if store_element else ''

        # 등록 시간
        time_element = row.select_one('time')
        time = time_element.get_text(strip=True) if time_element else ''

        # 댓글 수
        reply_element = title_element.select_one('span.info')
        reply_count = reply_element.get_text(strip=True) if reply_element else 0

        # 추천 수
        like_element = row.select_one('span.vcol.col-rate')
        like_count = like_element.get_text(strip=True) if like_element else 0

        # 이미지 url
        image_element = row.select_one(' a.title.preview-image')
        image_url = image_element['href'] if image_element else ''

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

