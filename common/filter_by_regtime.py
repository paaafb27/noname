"""
시간 필터링 유틸리티
"""
from datetime import datetime, timedelta, timezone
import re

# Python 표준 시간대 객체 (KST)
KST = timezone(timedelta(hours=9))
def filter_by_time(items, minutes=30):
    """
    등록시간 기준 N분 이내 게시글 필터링

    Args:
        items: 게시글 리스트
        minutes: 필터링 시간 (기본 30분)

    Returns:
        list: 필터링된 게시글 리스트
    """


    # timezone-aware로 cutoff_time 생성
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_time = now - timedelta(minutes=minutes)

    print(f"  [DEBUG] Cutoff Time: {cutoff_time}")

    filtered = []

    for item in items:
        try:
            time_str = item.get('crawledAt')
            if not time_str:
                continue

            article_time = parse_time(time_str)
            if not article_time:
                continue

            # timezone-aware로 변환 후 비교
            if article_time.tzinfo is None:
                article_time = article_time.replace(tzinfo=kst)

            # N분 이내만 수집
            if article_time >= cutoff_time:
                filtered.append(item)

        except Exception as e:
            print(f"시간 필터링 실패: {time_str}, 에러: {e}")
            continue

    return filtered


def parse_iso8601(time_str):
    """
    ISO8601 형식 문자열을 datetime 객체로 변환

    Args:
        time_str: ISO8601 문자열 (예: 2025-10-23T22:36:00+09:00)

    Returns:
        datetime: datetime 객체 (timezone-aware)
        None: 파싱 실패 시
    """
    if not time_str or not isinstance(time_str, str):
        return None

    try:
        # ISO8601 표준 형식
        if 'T' in time_str:
            # +09:00 형식 처리
            if '+' in time_str or time_str.endswith('Z'):
                return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            else:
                # 타임존 없는 경우 KST 추가
                dt = datetime.fromisoformat(time_str)
                kst = timezone(timedelta(hours=9))
                return dt.replace(tzinfo=kst)
    except:
        pass

    return None


def parse_time(time_str):
    """
    다양한 시간 문자열을 datetime 객체로 변환

    None: 파싱 실패 시
    """
    if not time_str:
        return None

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    time_str = time_str.strip()

    try:
        # 상대 시간 ("N분 전", "N시간 전" 등)
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

        # "YYYY-MM-DDTHH:MM:SS+09:00" (ISO 8601)
        if 'T' in time_str:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

        # "YYYY-MM-DD HH:MM" 형식
        if '-' in time_str and ':' in time_str:

            try:
                # 초(second)가 있는 형식 먼저 시도
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                return dt.replace(tzinfo=kst)
            except ValueError:
                try:
                    # 초(second)가 없는 형식 시도
                    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                    return dt.replace(tzinfo=kst)
                except ValueError:
                    # "MM-DD HH:MM" 형식 시도
                    try:
                        parsed = datetime.strptime(time_str, '%m-%d %H:%M')
                        dt = parsed.replace(year=now.year)
                        return dt.replace(tzinfo=kst)
                    except ValueError:
                        pass  # 다른 형식일 수 있으므로 계속 진행

        # "HH:MM:SS" 형식 (당일)
        if ':' in time_str and 'T' not in time_str and '-' not in time_str and '.' not in time_str and '/' not in time_str:
            try:
                if len(time_str.split(':')) == 3:
                    parsed = datetime.strptime(time_str, '%H:%M:%S')
                else:
                    parsed = datetime.strptime(time_str, '%H:%M')

                article_time = now.replace(hour=parsed.hour, minute=parsed.minute,
                                           second=parsed.second if hasattr(parsed, 'second') else 0, microsecond=0)

                # 만약 파싱된 시간이 현재 시간보다 미래라면, 하루를 뺍니다
                # 예: 현재 00:10, 게시글 23:50 -> 어제 23:50으로 처리
                if article_time > now:
                    article_time -= timedelta(days=1)

                return article_time

            except ValueError:
                pass

        # "YYYY.MM.DD" 형식 (루리웹)
        if '.' in time_str and len(time_str.split('.')) == 3:

            try:
                dt = datetime.strptime(time_str, '%Y.%m.%d')
                return dt.replace(tzinfo=kst)
            except ValueError:
                try:
                    # 2. 4자리 연도가 실패하면, 2자리 연도 (YY.MM.DD) 형식 시도
                    dt = datetime.strptime(time_str, '%y.%m.%d')
                    return dt.replace(tzinfo=kst)
                except ValueError:
                    # 두 형식 모두 실패하면 다음 로직으로
                    pass

        # "YYYY/MM/DD" 형식
        if '/' in time_str:
            try:
                dt = datetime.strptime(time_str, '%Y/%m/%d')
                return dt.replace(tzinfo=kst)
            except:
                pass



        # "MM-DD HH:MM" 형식 (올해)
        if '-' in time_str and ':' in time_str:
            try:
                parsed = datetime.strptime(time_str, '%m-%d %H:%M')
                dt = parsed.replace(year=now.year)
                return dt.replace(tzinfo=kst)
            except:
                pass


        return None

    except Exception as e:
        print(f"[시간 파싱 실패] {time_str}: {e}")
        return None


def to_iso8601(dt):
    """
    datetime 객체를 ISO8601 문자열로 변환

    Args:
        dt: datetime 객체, 문자열, 또는 None

    Returns:
        str: ISO8601 문자열 (예: 2025-10-23T22:36:00+09:00)
        None: dt가 None인 경우
    """
    if dt is None:
        return None

    # 이미 문자열인 경우
    if isinstance(dt, str):
        # 이미 ISO8601 형식인지 확인
        if 'T' in dt:
            return dt
        # 아닌 경우 파싱 후 변환 시도
        parsed = parse_time(dt)
        if parsed:
            dt = parsed
        else:
            return None

    # datetime 객체를 ISO8601로 변환
    kst = timezone(timedelta(hours=9))

    # timezone이 없으면 KST 추가
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=kst)

    return dt.isoformat()