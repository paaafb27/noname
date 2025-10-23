"""
루리웹 크롤러

URL: https://bbs.ruliweb.com/market/board/1020
필터링: notice, company, best 클래스 제외
판매처: <span class="subject_tag"> 또는 제목에서 추출
"""
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sys
import os
import re

from common.log_util import log_item

# common 모듈
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.filter_by_regtime import filter_by_time, parse_time, to_iso8601
from common.number_extractor import extract_price_from_title, extract_shipping_fee_from_title


class RuliwebScraper:

    def __init__(self):
        self.url = 'https://bbs.ruliweb.com/market/board/1020'
        self.main_url = 'https://bbs.ruliweb.com'
        self.source_site = 'RULIWEB'
        self.max_pages = 5
        self.test_mode = False

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

        kst = datetime.timezone(datetime.timedelta(hours=9))
        # 테스트 모드면 2시간, 실제는 30분
        filter_minutes = 120 if self.test_mode else 30
        now = datetime.datetime.now(kst)
        cutoff_time = now - datetime.timedelta(minutes=filter_minutes)

        while page_num <= self.max_pages:
            print(f"\n{page_num}페이지 크롤링 중...")

            page_items = self._scrape_page(page_num)

            if not page_items:
                print(f"{page_num}페이지: 게시글 없음, 종료")
                break

            # 30분 이내 작성된 게시글 필터링
            page_filtered = filter_by_time(page_items, minutes=filter_minutes)
            if page_filtered:
                print(f"  -> 수집 대상 {len(page_filtered)}개:")
                for filtered_item in page_filtered:
                    log_item(filtered_item)

            all_items.extend(page_filtered)
            print(f"{page_num}페이지: {len(page_items)}개 → 필터링 {len(page_filtered)}개")

            # 다음 페이지 확인 여부 판단
            # 원본(page_items)의 마지막 게시글 시간으로 판단
            last_item = page_items[-1]
            last_time = parse_time(last_item.get('crawledAt', ''))

            if not last_time:
                print(f"  → 시간 파싱 실패, 크롤링 종료")
                break

            # 마지막 게시글 등록 시간이 30분 초과면 중단
            if last_time < cutoff_time:
                print(f"→ 마지막 게시글 {filter_minutes}분 초과 ({last_time.strftime('%H:%M:%S')}), 종료")
                break

            print(f"→ 마지막 게시글 {filter_minutes}분 이내 ({last_time.strftime('%H:%M:%S')}), 다음 페이지 확인")
            page_num += 1

        if page_num > self.max_pages:
            print(f"\n⚠️ 최대 페이지({self.max_pages}) 도달, 크롤링 종료")

        print(f"\n✅ 총 {len(all_items)}개 수집 완료")
        return all_items

    def _scrape_page(self, page_num):
        """특정 페이지 크롤링"""

        items = []
        options = Options()

        # AWS Lambda 환경인지 확인합니다. ('AWS_EXECUTION_ENV' 환경 변수 존재 여부로 판단)
        if os.environ.get('AWS_EXECUTION_ENV'):
            # Lambda 환경일 경우, 미리 설치된 드라이버와 브라우저 경로를 지정합니다.
            print("  (Lambda 환경에서 실행)")

            # image/css 차단 for 속도 향상
            options.add_experimental_option(
                "prefs", {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.stylesheets": 2
                }
            )
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--single-process')
            options.binary_location = '/opt/chrome-linux64/chrome'  # 크롬 브라우저 실행 파일 경로
            service = Service(executable_path='/opt/chromedriver-linux64/chromedriver')
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # 로컬 환경일 경우, Selenium이 자동으로 드라이버를 관리하도록 합니다.
            print("  (로컬 환경에서 실행)")
            driver = webdriver.Chrome(options=options)

        try:
            # 페이지 URL
            if page_num == 1:
                url = self.url
            else:
                url = f"{self.url}?page={page_num}"

            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # 게시글 목록
            rows = soup.select('.board_list_table tbody tr.blocktarget')
            print(f"페이지 {page_num}: {len(rows)}개 발견")

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
                        log_item(item)

                except Exception as e:
                    print(f"게시글 파싱 실패: {e}")
                    continue

        except Exception as e:
            print(f"  페이지 로딩 실패: {e}")

        finally:
            driver.quit()

        return items

    def _extract_item(self, row):
        """
        세일정보 추출
        """
        # 제목
        title_element = row.select_one('a.subject_link.deco')
        if not title_element:
            return None
        title = title_element.get_text(strip=True)

        # URL
        product_url = title_element['href']

        # 판매처
        # 1) element 확인
        # 2) 제목에서 [판매처] 추출
        store_element = row.select_one('span.subject_tag')
        if store_element:
            store = store_element.get_text(strip=True)
        else:
            store = '기타'

        # 카테고리
        category_element = row.select_one('td.divsn.text_over a')
        category = category_element.get_text(strip=True) if category_element else None

        # 가격
        price = extract_price_from_title(title)

        # 배송비
        shipping_fee = extract_shipping_fee_from_title(title, self.source_site)

        # 등록 시간
        time_element = row.select_one('td.time')
        if time_element:
            time_text = time_element.get_text(strip=True)
            # print(f"  [DEBUG] 원본 시간: {time_text}")
            time_obj = parse_time(time_text)
            if not time_obj:
                print(f"  [DEBUG] 파싱 실패!")
            time = to_iso8601(time_obj) if time_obj else None

        # 댓글 수
        reply_element = row.select_one('span.num_reply')
        reply_count = reply_element.get_text(strip=True) if reply_element else 0

        # 좋아요 수
        like_element = row.select_one('td.recomd')
        like_count = like_element.get_text(strip=True) if like_element else 0

        # 이미지 url
        image_url = None


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

