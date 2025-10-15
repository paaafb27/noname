"""
루리웹 크롤러

URL: https://bbs.ruliweb.com/market/board/1020
필터링: notice, company, best 클래스 제외
판매처: <span class="subject_tag"> 또는 제목에서 추출
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import sys
import os

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))
from time_filter import filter_by_time
from store_extractor import extract_store

class RuliwebScraper:

    def __init__(self):
        self.url = 'https://bbs.ruliweb.com/market/board/1020'
        self.source_site = 'RULIWEB'

    def scrape(self):

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
                page.wait_for_selector('tr.table_body', timeout=10000)

                # HTML 파싱
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 게시글 목록
                rows = soup.select('.board_list_table tbody tr.blocktarget')
                print(f"게시글 {len(rows)}개 발견")

                for row in rows:
                    try:
                        # 필터링 : 공지 / 광고 제외
                        classes = row.get('class', [])
                        if 'best' in classes:
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

        print(f"필터링 전: {len(items)}개")

        # 30분 기준 필터링
        filtered_items = filter_by_time(items, minutes=30)
        print(f"30분 필터링 후: {len(filtered_items)}개")

        return filtered_items

    def _extract_item(self, row):
        """
        세일정보 추출
        """
        # 제목 및 URL
        title_element = row.select_one('a.baseList-title')
        if not title_element:
            return None

        title = title_element.get_text(strip=True)
        product_url = 'https://bbs.ruliweb.com' + title_element['href']

        # 판매처
        # 1) element 확인
        # 2) 제목에서 [판매처] 추출
        store_element = row.select_one('span.subject_tag')
        if store_element:
            store = store_element.get_text(strip=True)
        else:
            store = extract_store(title, 'RULIWEB')

        # 등록 시간
        time_element = row.select_one('td.time')
        time_str = time_element.get_text(strip=True) if time_element else ''

        # 가격
        price = 0

        # 이미지 url
        image_url = None

        return {
            'title': title,
            'price': price,
            'storeName': store,
            'productUrl': product_url,
            'imageUrl': image_url,
            'sourceSite': self.source_site,
            'crawledAt': time_str
        }

