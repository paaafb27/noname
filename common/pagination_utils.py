"""
스크레이퍼별 페이지 처리 로직 공통화
"""
import datetime

from common.filter_by_regtime import filter_by_time, parse_time


def _scrape_all_items(self):
    """
    - 페이지의 마지막 게시글이 30분 이내면 다음 페이지 계속 확인
    - 마지막 게시글이 30분 초과하거나 최대 페이지 도달 시 중단
    """
    all_items = []
    page_num = 1
    max_page = 5
    cutoff_time = datetime.now() - datetime.timedelta(minutes=30)

    print(f"== test == {self.source_site} 크롤링 ")

    while page_num <= max_page:
        print(f"\n{page_num}페이지 크롤링 중...")

        page_items = self._scrape_page(page_num, self.url)

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

        # 마지막 게시글 등록 시간이 30분 초과면 중단
        if last_time < cutoff_time:
            print(f"→ 마지막 게시글 30분 초과 ({last_time.strftime('%H:%M:%S')}), 종료")
            break

        print(f"→ 마지막 게시글 30분 이내 ({last_time.strftime('%H:%M:%S')}), 다음 페이지 확인")
        page_num += 1

    if page_num > self.max_pages:
        print(f"\n⚠️ 최대 페이지({self.max_pages}) 도달, 크롤링 종료")

    print(f"\n✅ 총 {len(all_items)}개 수집 완료")
    return all_items
