"""
뽐뿌 크롤러

URL: https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu
필터링: 공지, 쇼핑뽐뿌, 핫딜, 쇼핑포럼 제외
판매처: <em class="subject_preface"> 또는 제목에서 추출
"""
import datetime


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sys
import os
import re

from webdriver_manager.core.os_manager import ChromeType

from common.log_util import log_item

# common 모듈
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.filter_by_regtime import filter_by_time, parse_time, to_iso8601
from common.number_extractor import extract_price_from_title, extract_shipping_fee_from_title, extract_number_from_text


class PpomppuScraper:

    def __init__(self):
        self.url = 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
        self.source_site = 'PPOMPPU'
        self.main_url = 'https://www.ppomppu.co.kr/zboard/'
        self.max_pages = 5  # 최대 페이지 제한 (무한 루프 방지)
        self.test_mode = False

        # 환경 변수에서 필터링 시간 읽기 (기본값 30분)
        self.filter_minutes = int(os.environ.get('FILTER_MINUTES', 30))

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
        driver = None

        kst = datetime.timezone(datetime.timedelta(hours=9))
        filter_minutes = self.filter_minutes
        now = datetime.datetime.now(kst)
        cutoff_time = now - datetime.timedelta(minutes=filter_minutes)

        try:
            driver = self._create_driver()
            print("Chrome 브라우저 시작")

            while page_num <= self.max_pages:
                print(f"\n{page_num}페이지 크롤링...")

                # ✅ 같은 driver 재사용
                page_items = self._scrape_page(driver, page_num)

                if not page_items:
                    print(f"{page_num}페이지: 게시글 없음, 종료")
                    break

                # 30분 이내 작성된 게시글 필터링
                page_filtered = filter_by_time(page_items, minutes=filter_minutes)
                if page_filtered:
                    print(f"수집 대상 {len(page_filtered)}개:")
                    for filtered_item in page_filtered:
                        log_item(filtered_item)

                all_items.extend(page_filtered)
                print(f"{page_num}페이지: {len(page_items)}개 → 필터링 {len(page_filtered)}개")

                # 다음 페이지 확인 여부 판단
                last_item = page_items[-1]
                last_time = parse_time(last_item.get('crawledAt', ''))

                if not last_time:
                    print(f"시간 파싱 실패, 크롤링 종료")
                    break

                if last_time < cutoff_time:
                    print(f"마지막 게시글 {filter_minutes}분 초과 ({last_time.strftime('%H:%M:%S')}), 종료")
                    break

                print(f"마지막 게시글 {filter_minutes}분 이내 ({last_time.strftime('%H:%M:%S')}), 다음 페이지 확인")

                # 페이지 간 메모리 정리
                driver.execute_script("window.stop();")
                driver.delete_all_cookies()

                page_num += 1

            if page_num > self.max_pages:
                print(f"\n최대 페이지({self.max_pages}) 도달, 크롤링 종료")

            print(f"\n총 {len(all_items)}개 수집\n")
            return all_items

        except Exception as e:
            print(f"크롤링 실패: {e}")
            import traceback
            traceback.print_exc()
            return all_items            # 수집된 데이터라도 반환

        finally:
            if driver:
                try:
                    driver.quit()
                    print("Chrome 브라우저 정상 종료")
                except Exception as e:
                    print(f"Chrome 종료 중 에러: {e}")

    def _create_driver(self):
        options = Options()
        user_agent_string = "Mozilla/5.0 (Windows NT 1.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

        # --- Fargate/Lambda 공통 옵션 (최소 옵션 유지) ---
        print("(컨테이너 환경에서 실행 - WebDriverManager 사용)")

        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={user_agent_string}')

        # [수정] 임시 디렉토리 옵션은 충돌 가능성이 있으므로 일단 제거하고 테스트
        # options.add_argument('--user-data-dir=/tmp/chrome-user-data')
        # options.add_argument('--disk-cache-dir=/tmp/chrome-cache-dir')
        # options.add_argument('--data-path=/tmp/chrome-data-path')

        try:
            print("WebDriverManager로 Chromedriver 경로 확인 및 드라이버 생성 시도...")
            # 💡 [필수 수정] WebDriverManager 사용
            #   Service 객체에 자동으로 드라이버 경로를 찾아 전달
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            # service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("Chrome 드라이버 생성 성공!")
            driver.set_page_load_timeout(60)
            return driver
        except Exception as e:
            print(f"!!!!!!!! Chrome 드라이버 생성 실패 !!!!!!!!!!")
            print(f"오류: {e}")
            # WebDriverManager 로그 확인을 위해 traceback 추가
            import traceback
            traceback.print_exc()
            raise # 에러 다시 발생
        else:
            print("  (로컬 환경에서 실행)")
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument(f'--user-agent={user_agent_string}')
            options.add_argument('--window-size=1920,1080')
            driver = webdriver.Chrome(options=options)

        # 타임아웃 설정 (공통)
        driver.set_page_load_timeout(60)
        return driver

    def _scrape_page(self, driver, page_num):
        """
        개별 페이지 크롤링
        """
        items = []
        html = None

        try:
            if page_num == 1:
                url = self.url
            else:
                url = f"{self.url}&page={page_num}"

            driver.get(url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#revolution_main_table'))
                )
                print("게시글 로드 확인")
            except Exception as e:
                # 타임아웃 되어도 계속 진행 (부분 데이터라도 수집)
                print(f"명시적 대기 타임아웃 (계속 진행): {e}")

            # HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # 게시글 목록
            rows = soup.select('#revolution_main_table tbody tr.baseList')
            print(f"페이지 {page_num}: {len(rows)}개 발견")

            # 다른 선택자들도 시도
            if len(rows) == 0:
                print(f"  [DEBUG] 다른 선택자 시도...")
                alternative_rows = soup.select('#revolution_main_table')
                print(f"  [DEBUG] 대체 선택자: {len(alternative_rows)}개")

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

        except Exception as e:
            print(f"페이지 로딩 실패: {e}")
            import traceback
            traceback.print_exc()

        finally:
            html = None
            soup = None

        return items

    def _is_excluded(self, row):
        """
        제외 조건:
        - 글번호 영역에 <img> 태그 포함 (쇼핑뽐뿌, 핫딜, 쇼핑포럼)
        """
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
        # product_url = self.main_url + title_element['href']
        href = title_element.get('href', '')
        if not href:
            print(f"  ⚠️ href 속성 없음 (제목: {title[:30]}...)")
            return None
        product_url = self.main_url + href

        # 판매처
        # 제목에서 추출
        store_element = title_element.select_one('em.baseList-head.subject_preface')
        if store_element:
            store = store_element.get_text(strip=True)
        else:
            store = '기타'

        # 카테고리
        category_element = row.select_one('small.baseList-small')
        category = category_element.get_text(strip=True) if category_element else None

        # 가격
        price = extract_price_from_title(title)

        # 배송비
        shipping_fee = extract_shipping_fee_from_title(title, self.source_site)

        # 등록 시간
        time = None
        time_element = row.select_one('time.baseList-time')
        if time_element:
            time_text = time_element.get_text(strip=True)
            time_obj = parse_time(time_text)
            time = to_iso8601(time_obj) if time_obj else None

        # 댓글 수
        reply_count = 0
        reply_element = title_element.select_one('span.baseList-c')
        if reply_element:
            reply_text = reply_element.get_text(strip=True)
            reply_count = extract_number_from_text(reply_text)

        # 좋아요 수
        like_count = 0
        like_element = row.select_one('td.baseList-rec')
        if like_element:
            like_text = like_element.get_text(strip=True)
            like_count = extract_number_from_text(like_text)

        # 이미지 url
        image_element = row.select_one('a.baseList-thumb img')
        image_url = image_element.get('src') if image_element else None

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
