"""
스크레이퍼별 페이지 처리 로직 공통화
"""

from playwright.sync_api import Page
from typing import List, Callable
import time


def scrape_with_pagination(
        page: Page,
        max_pages: int,
        next_button_selector: str,
        extract_items_func: Callable,
        filter_func: Callable = None
) -> List[dict]:
    """
    페이지네이션 처리

    Args:
        page: Playwright Page 객체
        max_pages: 최대 페이지 수 (기본 2)
        next_button_selector: 다음 페이지 버튼 셀렉터
        extract_items_func: 아이템 추출 함수
        filter_func: 필터 함수 (30분 이내 확인용)

    Returns:
        list: 수집된 아이템 목록
    """
    all_items = []

    for page_num in range(1, max_pages + 1):
        print(f"📄 페이지 {page_num} 크롤링 중...")

        # 페이지 이동 (2페이지부터)
        if page_num > 1:
            try:
                # 다음 페이지 버튼 클릭
                next_btn = page.query_selector(next_button_selector)
                if not next_btn:
                    print(f"ℹ️ {page_num}페이지 없음, 종료")
                    break

                next_btn.click()
                page.wait_for_load_state('domcontentloaded')
                time.sleep(1)  # 로딩 대기

            except Exception as e:
                print(f"⚠️ 페이지 이동 실패: {e}")
                break

        # 아이템 추출
        try:
            items = extract_items_func(page)
            all_items.extend(items)

            print(f"✅ 페이지 {page_num}: {len(items)}개 수집")

        except Exception as e:
            print(f"❌ 페이지 {page_num} 크롤링 실패: {e}")
            break

        # 2페이지에서 최근 게시글 확인
        if page_num == 2 and filter_func:
            recent_items = filter_func(items)

            if len(recent_items) == 0:
                print("ℹ️ 2페이지에 30분 이내 게시글 없음, 종료")
                break

    return all_items