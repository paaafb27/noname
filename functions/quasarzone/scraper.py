"""
QUASARZONE 크롤러

URL: https://quasarzone.com/bbs/qb_saleinfo
"""

from datetime import datetime, timezone, timedelta
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
from common.number_extractor import extract_shipping_fee
from common.store_extractor import extract_store
from common.filter_by_regtime import filter_by_time, parse_time, to_iso8601
from common.parse_universal_time import _parse_universal_time

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))


class QuasarzoneScraper:

    def __init__(self):
        self.url = 'https://quasarzone.com/bbs/qb_saleinfo'
        self.main_url = 'https://quasarzone.com'
        self.source_site = 'QUASARZONE'
        self.max_pages = 3  # 최대 페이지 제한 (무한 루프 방지)
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

        filter_minutes = self.filter_minutes
        # 타임존 및 시간 기준 설정 (KST = UTC+9)
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        cutoff_time = now - timedelta(minutes=filter_minutes)
        print(f"크롤링 실행 시간 (KST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"수집 기준 시간 (KST): {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            driver = self._create_driver()
            print(f"Chrome 브라우저 시작 : {self.url}")

            while page_num <= self.max_pages:
                print(f"\n{page_num}페이지 크롤링...")

                # 같은 driver 재사용
                page_items = self._scrape_page(driver, page_num)

                if not page_items:
                    print(f"{page_num}페이지: 게시글 없음, 종료")
                    break

                # 30분 이내 작성된 게시글 필터링
                # page_filtered = filter_by_time(page_items, minutes=filter_minutes)
                page_filtered = self.filter_by_time_aware(page_items, cutoff_time)

                if page_filtered:
                    print(f"수집 대상 {len(page_filtered)}개:")
                    for filtered_item in page_filtered:
                        log_item(filtered_item)

                all_items.extend(page_filtered)
                print(f"{page_num}페이지: {len(page_items)}개 → 필터링 {len(page_filtered)}개")

                # 다음 페이지 확인 여부 판단
                last_item_in_page = page_items[-1]
                last_crawled_at_str = last_item_in_page.get('createdAt')  # 값이 없으면 None

                if not last_crawled_at_str:
                    print(f" [경고] 페이지 마지막 게시글의 시간 정보가 없어 다음 페이지를 계속 확인합니다.")

                else:
                    try:
                        # 크롤링된 시간 문자열('YYYY-MM-DD HH:mm:ss')을 Timezone이 없는(Naive) datetime 객체로 파싱
                        last_time_naive = datetime.strptime(last_crawled_at_str, '%Y-%m-%d %H:%M:%S')
                        # 파싱된 Naive 객체에 KST 타임존 정보를 부여하여 Aware 객체로 만듦
                        last_time_aware = last_time_naive.replace(tzinfo=kst)

                        # 이제 Aware 객체끼리 안전하게 비교 가능
                        if last_time_aware < cutoff_time:
                            print(f"페이지의 마지막 게시글 시간이 마지노선을 초과하여 크롤링을 종료합니다.")
                            print(
                                f" (마지막 글 시간: {last_time_aware.strftime('%H:%M:%S')} < 마지노선: {cutoff_time.strftime('%H:%M:%S')})")
                            break  # 루프 탈출
                        else:
                            print(f"페이지의 마지막 게시글 시간이 마지노선 이내이므로 다음 페이지를 확인합니다.")
                            print(
                                f" (마지막 글 시간: {last_time_aware.strftime('%H:%M:%S')} >= 마지노선: {cutoff_time.strftime('%H:%M:%S')})")

                    except ValueError:
                        # 'YYYY-MM-DD HH:mm:ss' 형식이 아닌 경우 (이론상 발생하면 안 됨)
                        print(f" [오류] createdAt 필드('{last_crawled_at_str}')의 형식이 올바르지 않아 다음 페이지를 계속 확인합니다.")
                    except Exception as e:
                        print(f" [오류] 알 수 없는 시간 처리 오류: {e}. 다음 페이지를 계속 확인합니다.")

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

        # User-Agent 설정 (공통)
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 기본 옵션 (공통)
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--referer=https://www.google.com/')

        # 자동화 감지 우회
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            # ✅ 환경 자동 감지
            import platform
            is_windows = platform.system() == 'Windows'
            
            if is_windows:
                print("(로컬 Windows 환경 감지 - WebDriverManager 자동 설치)")
                # 로컬: WebDriverManager 사용
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            else:
                print("(Linux 컨테이너 환경 감지 - Fargate 경로 사용)")
                # Fargate: 고정 경로
                service = Service('/usr/local/bin/chromedriver')
            
            driver = webdriver.Chrome(service=service, options=options)
            print("Chrome 드라이버 생성 성공!")

            # WebDriver 속성 숨기기
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(60)
            return driver
            
        except Exception as e:
            print(f"Chrome 드라이버 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _scrape_page(self, driver, page_num):

        items = []
        html = None

        try:
            # 페이지 URL
            if page_num == 1:
                url = self.url
            else:
                url = f"{self.url}&page={page_num}"

            driver.get(url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.market-type-list"))
                )
                print("게시글 로드 확인")
            except Exception as e:
                # 타임아웃 되어도 계속 진행 (부분 데이터라도 수집)
                print(f"명시적 대기 타임아웃 (계속 진행): {e}")


            # HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # 게시글 목록
            rows = soup.select('div.market-type-list tbody tr')
            print(f"게시글 {len(rows)}개 발견")

            # 다른 선택자들도 시도
            if len(rows) == 0:
                print(f"  [DEBUG] 다른 선택자 시도...")
                alternative_rows = soup.select('div.market-type-list')
                print(f"  [DEBUG] 대체 선택자: {len(alternative_rows)}개")

            for row in rows:
                try:
                    # 데이터 추출
                    item = self._extract_item(row, driver)
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

    def _extract_item(self, row, driver):
        """
        세일정보 추출
        """
        import re

        # 제목
        title_element = row.select_one('tr span.ellipsis-with-reply-cnt')
        title = title_element.get_text(strip=True) if title_element else None

        # 가격 : ￦ 19,800 (KRW)
        price = None
        price_element = row.select_one('span.text-orange')
        if price_element:
            price_text = price_element.get_text(strip=True)
            price_match = re.search(r'[￦₩]\s*([0-9,]+)', price_text)
            if price_match:
                try:
                    price = int(price_match.group(1).replace(',', ''))
                except:
                    pass

        # 배송비
        shipping_fee_element = row.select_one('div.market-info-sub > p:first-of-type > span:last-of-type')
        shipping_fee = shipping_fee_element.get_text(strip=True) if price_element else None
        shipping_fee = extract_shipping_fee(shipping_fee)

        # 판매처
        store = extract_store(title, self.source_site)
        """
        if store:
            store_match = re.match(r'\[([^\]]+)\]', title)
            if store_match:
                store = store_match.group(1)
                title = title[store_match.end():].strip()
        """

        # 댓글 수
        reply_element = row.select_one('span.board-list-comment span.ctn-count')
        reply_count = reply_element.get_text(strip=True) if reply_element else 0

        # 좋아요 수
        like_element = row.select_one('span.num.num.tp2')
        like_count = like_element.get_text(strip=True) if like_element else 0

        # 카테고리
        category_element = row.select_one('span.category')
        category = category_element.get_text(strip=True) if category_element else None

        # URL
        url_element = row.select_one('p.tit a')
        product_url = self.main_url + url_element['href']

        # 이미지 url
        image_element = row.select_one('a.thumb img')
        image_url = image_element['src'] if image_element else None

        # 등록 시간
        created_at = None
        time_element = row.select_one('span.date')

        try:
            current_url = driver.current_url  # 현재 URL 저장
            driver.get(product_url)

            # time_element_selector = 'div.util-area span.date'
            wait = WebDriverWait(driver, 30)
            detail_time_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.util-area span.date')))

            time_text = detail_time_element.text

            # 원래 페이지로 복귀
            driver.get(current_url)

        except Exception as e:
            print("상세페이지 접속 실패")
            time_text = time_element.text

        created_at = _parse_universal_time(time_text)
        print(f"created_at : {created_at}")

        print(f"title : {title} | time : {created_at}")

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
            'createdAt': created_at
        }

    def _parse_universal_time(self, time_text):
        """
        다양한 형태의 시간 문자열을 파싱하여 timezone-aware datetime 객체로 변환합니다.
        - "N분 전", "N시간 전", "방금"
        - "HH:mm", "HH:mm:ss"
        - "YYYY-MM-DD", "YY-MM-DD", "YYYY.MM.DD", "YY.MM.DD"
        - ISO 8601 형식 (예: "2025-10-31T15:30:00+09:00")
        """
        import re
        from datetime import datetime, timezone, timedelta

        # KST 타임존 설정
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        time_text = time_text.strip()

        try:
            # ISO 8601 형식 (가장 정확한 정보)
            if 'T' in time_text and ('+' in time_text or 'Z' in time_text):
                # Python 3.11+ 에서는 Z를 바로 파싱 가능, 하위 호환성을 위해 Z를 +00:00으로 변경
                if time_text.endswith('Z'):
                    time_text = time_text[:-1] + '+00:00'
                return datetime.fromisoformat(time_text)

            # "N분 전" 형식
            if '분 전' in time_text:
                minutes_ago = int(re.search(r'(\d+)', time_text).group(1))
                return now - timedelta(minutes=minutes_ago)

            # "N시간 전" 형식
            if '시간 전' in time_text:
                hours_ago = int(re.search(r'(\d+)', time_text).group(1))
                return now - timedelta(hours=hours_ago)

            # "방금" 형식
            if '방금' in time_text:
                return now

            # "HH:mm" 또는 "HH:mm:ss" 형식 (오늘 날짜)
            if ':' in time_text and '-' not in time_text and '.' not in time_text and '/' not in time_text:
                parts = list(map(int, time_text.split(':')))
                hour = parts[0]
                minute = parts[1]
                second = parts[2] if len(parts) > 2 else 0
                return now.replace(hour=hour, minute=minute, second=second, microsecond=0)

            # "YYYY-MM-DD" 또는 "YY-MM-DD" 형식
            # "YYYY-MM-DD" 또는 "YY-MM-DD" 또는 "MM-DD" 또는 "YYYY-MM-DD HH:mm" 형식 (★★★★★ v4 변경점 ★★★★★)
            if '-' in time_text:
                parts = time_text.split()
                date_part = parts[0]

                # "YYYY-MM-DD HH:mm" 형식
                if len(parts) > 1 and ':' in parts[1]:
                    return datetime.strptime(time_text, '%Y-%m-%d %H:%M').replace(tzinfo=kst)

                # "YYYY-MM-DD", "YY-MM-DD", "MM-DD" 형식
                else:
                    date_parts = date_part.split('-')
                    if len(date_parts) == 3:
                        return datetime.strptime(date_part,
                                                     '%Y-%m-%d' if len(date_parts[0]) == 4 else '%y-%m-%d').replace(tzinfo=kst)
                    elif len(date_parts) == 2:
                        return datetime.strptime(f"{now.year}-{date_part}", '%Y-%m-%d').replace(tzinfo=kst)

            # "YYYY.MM.DD" 또는 "YY.MM.DD" 형식
            if '.' in time_text:
                return datetime.strptime(time_text,
                                         '%Y.%m.%d' if len(time_text.split('.')[0]) == 4 else '%y.%m.%d').replace(
                    tzinfo=kst)

            # 그 외 처리 불가
            return None

        except Exception as e:
            print(f"  [PARSING-ERROR] 범용 시간 파싱 실패: '{time_text}', 오류: {e}")
            return None


    def filter_by_time_aware(self, items, cutoff_time):
        """
        Timezone을 인지(aware)하여 아이템 리스트를 필터링하는 함수.

        :param items: 크롤링된 아이템 딕셔너리의 리스트
        :param cutoff_time: Timezone 정보가 포함된(aware) 기준 시간 datetime 객체
        :return: 필터링된 아이템 리스트
        """
        kst = timezone(timedelta(hours=9))

        filtered_list = []
        for item in items:
            created_at_str = item.get('createdAt')
            if not created_at_str:
                continue  # 시간 정보 없으면 건너뛰기

            try:
                # 크롤링된 시간 문자열을 Timezone 없는(Naive) datetime 객체로 파싱
                item_time_naive = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')

                # 파싱된 Naive 객체에 KST 타임존 정보를 부여하여 Aware 객체로 만듦
                item_time_aware = item_time_naive.replace(tzinfo=kst)

                # Aware 객체끼리 비교하여 최신 글만 리스트에 추가
                if item_time_aware >= cutoff_time:
                    filtered_list.append(item)

            except Exception as e:
                print(f"  [FILTER-ERROR] '{created_at_str}' 시간 필터링 중 오류: {e}")
                continue

        return filtered_list