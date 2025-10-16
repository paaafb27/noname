"""
ARCALIVE 크롤러

URL: https://arca.live/b/hotdeal
"""
import datetime
import sys
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from common.filter_by_regtime import filter_by_time, parse_time

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))


class ArcaliveScraper:

    def __init__(self):
        self.url = 'https://arca.live/b/hotdeal'
        self.main_url = "https://arca.live"
        self.source_site = 'ARCALIVE'
        self.max_pages = 5

    def scrape(self):
        """페이징 크롤링 (30분 필터링)"""
        return self._scrape_with_pagination()

    def _scrape_with_pagination(self):
        """
        - 페이지의 마지막 게시글이 30분 이내면 다음 페이지 계속 확인
        - 마지막 게시글이 30분 초과하거나 최대 페이지 도달 시 중단
        """
        all_items = []
        page_num = 1
        cutoff_time = datetime.now() - datetime.timedelta(minutes=30)

        while page_num <= self.max_pages:
            print(f"\n{page_num}페이지 크롤링...")

            page_items = self._scrape_page(page_num)

            if not page_items:
                print(f"{page_num}페이지: 게시글 없음, 종료")
                break

            # 30분 이내 작성된 게시글 필터링
            page_filtered = filter_by_time(page_items, minutes=30)
            all_items.extend(page_filtered)
            print(f"{page_num}페이지: {len(page_items)}개 → 필터링 {len(page_filtered)}개")

            # 다음 페이지 확인 여부 판단
            # 원본(page_items)의 마지막 게시글 시간으로 판단
            last_item = page_items[-1]
            last_time = parse_time(last_item.get('crawledAt', ''))

            if not last_time:
                print(f"  → 시간 파싱 실패, 크롤링 종료")
                break

            if last_time < cutoff_time:
                print(f"→ 마지막 게시글 30분 초과 ({last_time.strftime('%H:%M:%S')}), 종료")
                break

            print(f"→ 마지막 게시글 30분 이내 ({last_time.strftime('%H:%M:%S')}), 다음 페이지 확인")
            page_num += 1

        if page_num > self.max_pages:
            print(f"\n⚠️ 최대 페이지({self.max_pages}) 도달, 크롤링 종료")

        print(f"\n✅ 총 {len(all_items)}개 수집\n")
        return all_items

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
                # 페이지 URL
                if page_num == 1:
                    url = self.url
                else:
                    url = f"{self.url}&p={page_num}"

                # 페이지 로딩
                page.goto(
                    url,
                    timeout=30000,
                    wait_until='domcontentloaded'
                )
                # 테이블 로딩 대기
                page.wait_for_selector('div.list-table.hybrid', timeout=10000)

                # HTML 파싱
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 게시글 목록
                rows = soup.select('div.list-table.hybrid div.vrow.hybrid')
                print(f"페이지 {page_num}: {len(rows)}개 발견")

                for row in rows:
                    try:
                        item = self._extract_item(row)
                        if item:
                            items.append(item)

                    except Exception as e:
                        print(f"게시글 파싱 실패: {e}")
                        continue

            except Exception as e:
                print(f"  페이지 로딩 실패: {e}")

            finally:
                browser.close()

            return items

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

        # 카테고리
        category_element = row.select_one('a.badge')
        category = category_element.get(strip=True) if category_element else None

        # 가격
        price_element = row.select_one('span.deal-price')
        price = price_element.get_text(strip=True) if price_element else None

        # 배송비
        shipping_fee_element = row.select_one('span.deal-delivery')
        shipping_fee = shipping_fee_element.get_text(strip=True) if store_element else None

        # 등록 시간
        time_element = row.select_one('time')
        time = time_element.get_text(strip=True) if time_element else None

        # 댓글 수
        reply_element = title_element.select_one('span.info')
        reply_count = reply_element.get_text(strip=True) if reply_element else 0

        # 추천 수
        like_element = row.select_one('span.vcol.col-rate')
        like_count = like_element.get_text(strip=True) if like_element else 0

        # 이미지 url
        image_element = row.select_one('a.title.preview-image img')
        image_url = image_element['src'] if image_element else None

        return {
            'title': title,
            'price': price,
            'storeName': store,
            'category': category,
            'shippingFee': shipping_fee,
            'productUrl': product_url,
            'imageUrl': image_url,
            'replyCount': reply_count,
            'likeCount': like_count,
            'sourceSite': self.source_site,
            'crawledAt': time
        }

