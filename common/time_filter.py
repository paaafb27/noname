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
        try:
            time_str = item.get('crawledAt', '')

            if not time_str:
                continue

            # 절대 시간으로 변환
            article_time = parse_time(time_str)

            if not article_time:
                continue

            # 30분 이내만 수집
            if article_time >= cutoff_time:
                filtered.append(item)

        except Exception as e:
            print(f"시간 파싱 실패: {time_str}, 에러: {e}")

    return filtered

def parse_time(time_str):
    """
    시간 문자열을 datetime 객체로 변환
    """
    now = datetime.now()

    # 방금 전
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

    # "2025-01-01 00:00"
    try:
        return datetime.strptime(time_str, '%Y-%m-%d %H %M')
    except:
        pass

    # "01-01 00:30"
    try:
        parsed = datetime.strptime(time_str, '%m-%d %H:%M')
        return parsed.replace(year=now.year)
    except:
        pass

    # "2025.01.01" 형식
    try:
        return datetime.strptime(time_str, '%Y.%m.%d')
    except:
        pass

    # 8. ISO 8601 형식
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    except:
        pass

    return None