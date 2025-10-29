"""
EOMISAE 크롤러

URL: https://eomisae.co.kr/
"""
import datetime
import time

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
from common.number_extractor import extract_price_from_title, extract_number_from_text
from common.filter_by_regtime import filter_by_time, parse_time, to_iso8601
from common.store_extractor import extract_store

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))


class EomisaeScraper:

    def __init__(self):
        self.urls = [
            'https://eomisae.co.kr/os', # 패션정보
            'https://eomisae.co.kr/rt'  # 기타정보
            ]
        self.main_url = 'https://eomisae.co.kr/'
        self.source_site = 'EOMISAE'
        self.max_pages = 3
        self.test_mode = False

        # 환경 변수에서 필터링 시간 읽기 (기본값 30분)
        self.filter_minutes = int(os.environ.get('FILTER_MINUTES', 30))

    def scrape(self):

        all_items = []

        # 각 게시판 크롤링
        for url in self.urls:
            print(f"게시판 크롤링: {url}")
            items = self._scrape_with_pagination(url)
            all_items.extend(items)

        return all_items

    def _scrape_with_pagination(self, url):
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
            print(f"Chrome 브라우저 시작 : {url}")

            while page_num <= self.max_pages:
                print(f"\n{page_num}페이지 크롤링...")

                # 같은 driver 재사용
                page_items = self._scrape_page(driver, page_num, url)

                if not page_items:
                    print(f"{page_num}페이지: 게시글 없음, 종료")
                    break

                # 30분 이내 작성된 게시글 필터링
                page_filtered = filter_by_time(page_items, minutes=filter_minutes)
                if page_filtered:
                    print(f" 수집 대상 {len(page_filtered)}개:")
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

                # ✅ 페이지 간 메모리 정리
                driver.execute_script("window.stop();")
                driver.delete_all_cookies()

                page_num += 1

            if page_num > self.max_pages:
                print(f"\n최대 페이지({self.max_pages}) 도달, 크롤링 종료")

            print(f"\n총 {len(all_items)}개 수집\n")
            return all_items

        except Exception as e:
            print(f"❌ 크롤링 실패: {e}")
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

        # --- Fargate/Lambda 공통 옵션 (최소 옵션 유지) ---
        print("(컨테이너 환경에서 실행 - WebDriverManager 사용)")

        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--referer=https://www.google.com/')

        # 자동화 감지 우회
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # [수정] 임시 디렉토리 옵션은 충돌 가능성이 있으므로 일단 제거하고 테스트
        # options.add_argument('--user-data-dir=/tmp/chrome-user-data')
        # options.add_argument('--disk-cache-dir=/tmp/chrome-cache-dir')
        # options.add_argument('--data-path=/tmp/chrome-data-path')

        try:
            print("WebDriverManager로 Chromedriver 경로 확인 및 드라이버 생성 시도...")
            # 💡 [필수 수정] WebDriverManager 사용
            #   Service 객체에 자동으로 드라이버 경로를 찾아 전달
            service = Service('/usr/local/bin/chromedriver')
            # service = Service('/usr/local/bin/chromedriver').install())
            driver = webdriver.Chrome(service=service, options=options)
            print("Chrome 드라이버 생성 성공!")

            # WebDriver 속성 숨기기
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
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

    def _scrape_page(self, driver, page_num, targetUrl):
        """특정 페이지 크롤링"""
        items = []
        html = None

        try:
            # 페이지 URL
            if page_num == 1:
                url = targetUrl
            else:
                if 'os' in targetUrl:   # 패션
                    url = f"https://eomisae.co.kr/index.php?mid=os&page={page_num}"
                else:
                    url = f"https://eomisae.co.kr/index.php?mid=rt&page={page_num}"

            driver.get(url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.card_wrap"))
                )
                print("게시글 로드 확인")
            except Exception as e:
                # 타임아웃 되어도 계속 진행 (부분 데이터라도 수집)
                print(f"⚠️ 명시적 대기 타임아웃 (계속 진행): {e}")


            # HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # HTML 저장 (디버깅용)
            # with open(f'debug_{self.source_site}_page{page_num}.html', 'w', encoding='utf-8') as f:
                # f.write(html)
            #print(f"  [DEBUG] HTML 저장: debug_{self.source_site}_page{page_num}.html")

            # 게시글 목록
            cards = soup.select('div.card_el.n_ntc.clear')
            print(f"게시글 {len(cards)}개 발견")

            # 다른 선택자들도 시도
            if len(cards) == 0:
                print(f"  [DEBUG] 다른 선택자 시도...")
                alternative_rows = soup.select('div._bd.cf.clear')
                print(f"  [DEBUG] 대체 선택자: {len(alternative_rows)}개")

            for card in cards:
                try:
                    # 필터링
                    title_element = card.select_one('a.pjax')
                    title = title_element.get_text(strip=True)

                    # 레벨 미달 제외
                    if re.search(r'\d+분\s*뒤\s*전체\s*공개로\s*전환됩니다', title):
                        print(f"[어미새] 레벨 미달 제외: {title[:40]}...")
                        continue
                    # "미달 조건 : 레벨" 패턴
                    elif '미달 조건' in title and '레벨' in title:
                        print(f"[어미새] 레벨 미달 제외: {title[:40]}...")
                        continue

                    # 데이터 추출
                    item = self._extract_item(card, driver)
                    if item:
                        items.append(item)

                except Exception as e:
                    print(f"게시글 파싱 실패: {e}")
                    continue

        except Exception as e:
            print(f"    페이지 로딩 실패: {e}")
            import traceback
            traceback.print_exc()

        finally:
            html = None
            soup = None

        return items

    def _extract_item(self, card, driver):
        """
        세일정보 추출
        """
        # 제목
        title_element = card.select_one('a.pjax')
        if not title_element:
            return None
        title = title_element.get_text(strip=True)

        # URL
        product_url = title_element['href']
        if not product_url:
            return None

        # 상세 페이지 접속 후 시간 get
        try:
            driver.get(product_url)
            time_element_selector = 'span.fa.fa-clock-o + span'
            wait = WebDriverWait(driver, 10)  # 상세 페이지 로딩을 위한 대기
            time_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, time_element_selector)))

            time_text = time_element.text
            time_obj = parse_time(time_text)
            time = to_iso8601(time_obj)

        except Exception as e:
            print(f"  상세 페이지 시간 추출 실패: {product_url}, 에러: {e}")
            time = None  # 시간 추출 실패 시 None으로 처리

        # 판매처: 제목 첫 단어
        # ex) "금강제화 더비" → "금강제화"
        #first_word = title.split()[0] if title else '기타'
        store = extract_store(title)

        # 가격 : 일관된 형식 없음
        price = extract_price_from_title(title)

        # 배송비
        # title에 '무배' 키워드가 있으면 0 없으면 ''
        shipping_fee = ''

        # 댓글 수
        reply_element = card.select_one('div.card_content span:nth-of-type(2).fr')
        reply_count = reply_element.get_text(strip=True) if reply_element else None
        reply_count = extract_number_from_text(reply_count)

        # 추천 수
        like_element = card.select_one('div.card_content span:nth-of-type(3).fr')
        like_count = like_element.get_text(strip=True) if like_element else None
        like_count = extract_number_from_text(like_count)

        # 이미지 url
        img_element = card.select_one('div.tmb_wrp img.tmb')
        image_url = img_element['src'] if img_element else None

        return {
            'title': title,
            'price': price,
            'storeName': store,
            #'category': category,
            'shippingFee': shipping_fee,
            'productUrl': product_url,
            'imageUrl': image_url,
            'replyCount': reply_count,
            'likeCount': like_count,
            'sourceSite': self.source_site,
            'crawledAt': time
        }
