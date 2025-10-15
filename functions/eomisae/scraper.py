"""
EOMISAE 크롤러

URL: https://eomisae.co.kr/
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import sys
import os

from common.time_filter import filter_by_time

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))


class EomisaeScraper:

    def __init__(self):
        self.urls = [
            'https://eomisae.co.kr/os', # 패션정보
            'https://eomisae.co.kr/rt'  # 기타정보
            ]
        self.source_site = 'EOMISAE'

    def scrape(self):

        all_items = []

        # 각 게시판 크롤링
        for url in self.urls:
            print(f"게시판 크롤링: {url}")
            items = self._scrape_board(url)
            all_items.extend(items)

        print(f"전체 게시판 필터링 전: {len(all_items)}개")

        # 30분 필터링
        filtered = filter_by_time(all_items, minutes=30)
        print(f"30분 필터링 후: {len(filtered)}개")

        return filtered

    def _scrape_board(self, url):

        items = []

        with sync_playwright() as p:
            # 브라우저 실행
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
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
                page.wait_for_selector('div.card_el', timeout=10000)

                # HTML 파싱
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 게시글 목록
                cards = soup.select('div.card_el.n_ntc.clear')
                print(f"게시글 {len(cards)}개 발견")

            finally:
                browser.close()

        return items

    def _extract_item(self, card):
        """
        세일정보 추출
        """
        # 제목
        title_element = card.locator('a[class="pjax"]')
        if not title_element:
            return None
        title = title_element.get_text(strip=True)

        # URL
        product_url = title_element['href']

        # 판매처: 제목 첫 단어
        # ex) "금강제화 더비" → "금강제화"
        first_word = title.split()[0] if title else '기타'
        store = first_word

        # 가격 : 일관된 형식 없음
        price = ''

        # 배송비
        # title에 '무배' 키워드가 있으면 0 없으면 ''
        shipping_fee = ''

        # 등록 시간
        time_element = card.select_one('div.card_content span:nth-of-type(2):not(.fr)')
        time = time_element.get_text(strip=True) if time_element else ''

        # 댓글 수
        reply_element = card.select_one('div.card_content span:nth-of-type(2).fr')
        reply_count = reply_element.get_text(strip=True) if reply_element else None

        # 추천 수
        like_element = card.select_one('div.card_content span:nth-of-type(3).fr')
        like_count = like_element.get_text(strip=True) if like_element else None

        # 이미지 url
        img_element = card.select_one('div.card_el.n_ntc.clear div.tmb_wrp img.tmb')
        image_url = img_element['src'] if img_element else None

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

