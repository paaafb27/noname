"""
FMKOREA 크롤러

URL: https://www.fmkorea.com/hotdeal
"""
import datetime
import sys
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from common.log_util import log_item

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))
from common.number_extractor import extract_number_from_text
from common.filter_by_regtime import filter_by_time, parse_time, to_iso8601


class FmkoreaScraper:

    def __init__(self):
        self.url = 'https://www.fmkorea.com/hotdeal'
        self.main_url = 'https://www.fmkorea.com'
        self.source_site = 'FMKOREA'
        self.max_pages = 5
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
            return all_items        # 수집된 데이터라도 반환

        finally:
            if driver:
                try:
                    driver.quit()
                    print("Chrome 브라우저 정상 종료")
                except Exception as e:
                    print(f"Chrome 종료 중 에러: {e}")

    def _create_driver(self):
        options = Options()
        user_agent_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

        print("(컨테이너 환경에서 실행)")

        # 메모리 최적화 옵션
        options.add_experimental_option(
            "prefs", {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
                "profile.managed_default_content_settings.fonts": 2,
                "profile.managed_default_content_settings.plugins": 2,
                "profile.managed_default_content_settings.popups": 2,
            }
        )
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-breakpad')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f'--user-agent={user_agent_string}')
        options.add_argument('--disable-javascript')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--max-old-space-size=512')
        options.set_capability('pageLoadStrategy', 'eager')

        # [고정] 크롬/드라이버 경로
        options.binary_location = '/opt/chrome-linux64/chrome'
        service = Service(executable_path='/opt/chromedriver-linux64/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)

        driver.set_page_load_timeout(60)

        return driver


    def _scrape_page(self, driver, page_num):

        items = []
        html = None

        try:
            # 페이지 URL
            if page_num == 1:
                url = self.url
            else:
                url = f"{self.main_url}/index.php?mid=hotdeal&page={page_num}"

            # 페이지 로드
            driver.get(url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.fm_best_widget._bd_pc"))
                )
                print("게시글 로드 확인")
            except Exception as e:
                # 타임아웃 되어도 계속 진행 (부분 데이터라도 수집)
                print(f"명시적 대기 타임아웃 (계속 진행): {e}")


            # HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # 게시글 목록
            rows = soup.select('div.fm_best_widget._bd_pc li.li_best2_hotdeal0')
            print(f"게시글 {len(rows)}개 발견")

            # 다른 선택자들도 시도
            if len(rows) == 0:
                print(f"  [DEBUG] 다른 선택자 시도...")
                alternative_rows = soup.select('div.fm_best_widget._bd_pc')
                print(f"  [DEBUG] 대체 선택자: {len(alternative_rows)}개")

            for row in rows:
                try:
                    # 데이터 추출
                    item = self._extract_item(row)
                    if item:
                        items.append(item)

                except Exception as e:
                    print(f"게시글 파싱 실패: {e}")
                    continue

        except Exception as e:
            print(f"  페이지 로딩 실패: {e}")
            import traceback
            traceback.print_exc()

        finally:
            html = None
            soup = None

        return items

    def _extract_item(self, row):
        """
        세일정보 추출
        """
        try:
            # 제목
            title_element = row.select_one('span.ellipsis-target')
            if not title_element:
                return None
            title = title_element.get_text(strip=True)

            # URL
            url_element = row.select_one('div.li a.hotdeal_var8')
            if not url_element:
                print(f"  ⚠️ URL 없음 (제목: {title[:30]}...)")
                return None

            href = url_element.get('href', '')
            if not href:
                print(f"  ⚠️ href 속성 없음 (제목: {title[:30]}...)")
                return None
            product_url = self.main_url + url_element.get('href', '')

            # 판매처
            store_element = row.select_one('div.hotdeal_info span:nth-of-type(1) a.strong')
            if store_element:
                store = store_element.get_text(strip=True)
            else:
                store = '기타'

            # 카테고리
            category_element = row.select_one('span.category a')
            category = category_element.get_text(strip=True) if category_element else None

            # 가격
            price_element = row.select_one('div.hotdeal_info span:nth-of-type(2) a.strong')
            price = price_element.get_text(strip=True) if price_element else ''

            # 배송비
            # shipping_fee_selector = "//div[@class='fm_best_widget _bd_pc']//li[contains(@class, 'li_best2_hotdeal0')]//span[contains(text(), '배송')]/a[@class='strong']"
            shipping_fee_element = row.select_one('div.hotdeal_info span:nth-of-type(3) a.strong')
            shipping_fee = shipping_fee_element.get_text(strip=True) if shipping_fee_element else None

            # 등록 시간
            time = None
            time_element = row.select_one('span.regdate')
            if time_element:
                time_text = time_element.get_text(strip=True)
                time_obj = parse_time(time_text)
                time = to_iso8601(time_obj) if time_obj else None

            # 댓글 수
            reply_count = 0
            reply_element = row.select_one('span.comment_count')
            if reply_element:
                reply_text = reply_element.get_text(strip=True)
                reply_count = extract_number_from_text(reply_text)

            # 추천 수
            like_count = 0
            like_element = row.select_one('span.count')
            if like_element:
                like_text = like_element.get_text(strip=True)
                like_count = extract_number_from_text(like_text)

            # 이미지 url
            image_element = row.select_one('img.thumb')
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

        except Exception as e:
            print(f"항목 추출 중 오류: {e}")
            return None
