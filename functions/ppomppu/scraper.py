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

from common.time_filter import filter_by_time

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

class PpomppuScraper:

    def __init__(self):
        self.url = 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
        self.source_site = 'PPOMPPU'
        self.main_url = 'https://www.ppomppu.co.kr/zboard/'

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
                page.wait_for_selector('#revolution_main_table', timeout=10000)

                # HTML 파싱
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 게시글 목록
                rows = soup.select('#revolution_main_table tbody tr.baseList.bbs_new1')
                print(f"게시글 {len(rows)}개 발견")

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

        print(f"필터링 전: {len(items)}개")

        # 30분 기준 필터링
        filtered_items = filter_by_time(items, minutes=30)

        print(f"30분 필터링 후: {len(filtered_items)}개")

        return filtered_items

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

    def _extract_item(self, row):
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
        #price_str = await title_element.inner_text()

        # 배송비
        #shipping_fee_element = row.select_one('span.deal-delivery')
        #shipping_fee = shipping_fee_element.get_text(strip=True) if store_element else ''

        # 등록 시간
        time_element = row.select_one('time.baseList-time')
        time = time_element.get_text(strip=True) if time_element else ''

        # 댓글 수
        reply_element = title_element.select_one('span.baseList-c')
        reply_count = reply_element.get_text(strip=True) if reply_element else 0

        # 추천 수
        like_element = row.title_element('td.baseList-rec')
        like_count = like_element.get_text(strip=True) if like_element else 0

        # 이미지 url
        image_element = row.select_one('a.baseList-thumb')
        image_url = self.main_url + image_element['href']

        return {
            'title': title,
            #'price': price,
            'storeName': store,
            #'shippingFee': shipping_fee,
            'productUrl': product_url,
            'imageUrl': image_url,
            'replyCount': reply_count,
            'likeCount': like_count,
            'sourceSite': self.source_site,
            'crawledAt': time
        }

