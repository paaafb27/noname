"""
시간 필터링 유틸리티
"""
from datetime import datetime, timedelta
import re

def filter_by_time(items, minutes=30):
    """
    등록시간 기준 30분 이내
    """
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    filtered = []

    for item in items:
        time_str = item.get('crawledAt', '')
        if not time_str:
            continue

        # 시간 문자열을 datetime 객체로 변환
        article_time = parse_time(time_str)
        if not article_time:
            continue

    return filtered

def parse_time(time_str):
    """
    시간 문자열을 datetime 객체로 변환
    """
    now = datetime.now()

    try:
        # 방금 전 or 초
        if '방금' in time_str or '초' in time_str:
            return now

        # N분 전
        match = re.search(r'(\d+)분\s*전', time_str)
        if match:
            minutes = int(match.group(1))
            return now - timedelta(minutes=minutes)

        # N시간 전
        match = re.search(r'(\d+)시간\s*전', time_str)
        if match:
            hours = int(match.group(1))
            return now - timedelta(hours=hours)

        # N일 전
        match = re.search(r'(\d+)일\s*전', time_str)
        if match:
            days = int(match.group(1))
            return now - timedelta(days=days)

        # "00:00:00" 형식 (당일)
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 3:
                parsed = datetime.strptime(time_str, '%H:%M:%S')
                return now.replace(
                    hour=parsed.hour,
                    minute=parsed.minute,
                    second=parsed.second,
                    microsecond=0
                )
            elif len(parts) == 2:
                parsed = datetime.strptime(time_str, '%H:%M')
                return now.replace(
                    hour=parsed.hour,
                    minute=parsed.minute,
                    second=0,
                    microsecond=0
                )

        # "2025-01-15 14:30"
        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M')
        except:
            pass

        # "2025/01/15" 형식
        if '/' in time_str:
            return datetime.strptime(time_str, '%Y/%m/%d')

        # "01-15 14:30" 형식
        if '-' in time_str and ':' in time_str:
            parsed = datetime.strptime(time_str, '%m-%d %H:%M')
            return parsed.replace(year=now.year)

        return None

    except Exception as e:
        print(f"[시간 파싱 실패] {time_str}: {e}")
        return None