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

    print(f"  [FILTER] 현재 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  [FILTER] Cutoff 시각: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} ({minutes}분 전)")

    filtered = []

    for item in items:
        try:
            time_str = item.get('crawledAt')
            if not time_str:
                continue

            # 'yyyy-MM-dd HH:mm:ss' 형식이면 직접 파싱
            if len(time_str) == 19 and time_str[10] == ' ':
                article_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                article_time = article_time.replace(tzinfo=kst)
            else:
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

def parse_time(time_str):
    """
    다양한 시간 문자열을 datetime 객체로 변환

    None: 파싱 실패
    """
    if not time_str:
        return None

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    time_str = time_str.strip()
    print(f"time_str = {time_str}")

    try:
        # 'yyyy-MM-dd HH:mm:ss'
        if len(time_str) == 19 and time_str[10] == ' ':
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            return dt.replace(tzinfo=kst)

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
            print("test")

            try:
                # 초(second)가 있는 형식 먼저 시도
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                return dt.replace(tzinfo=kst)
            except ValueError:
                try:
                    # 초(second)가 없는 형식 시도
                    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                    print(f"{dt.replace(tzinfo=kst)}")
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
            print("HH:MM:SS type")
            try:
                if len(time_str.split(':')) == 3:
                    parsed = datetime.strptime(time_str, '%H:%M:%S')
                else:
                    parsed = datetime.strptime(time_str, '%H:%M')

                article_time = now.replace(hour=parsed.hour, minute=parsed.minute,
                                           second=parsed.second if len(time_str.split(':')) == 3 else 0,
                                           microsecond=0)

                # 미래 시간이면 어제로 처리
                if article_time > now:
                    article_time -= timedelta(days=1)

                print(f"article_time : {article_time}")
                return article_time

            except ValueError:
                pass

            # YYYY-MM-DD HH:MM:SS 형식 (초 포함)
            if '-' in time_str and ':' in time_str:
                try:
                    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    return dt.replace(tzinfo=kst)
                except ValueError:
                    try:
                        # 초 없는 형식
                        dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                        return dt.replace(tzinfo=kst)
                    except ValueError:
                        # MM-DD HH:MM 형식
                        try:
                            parsed = datetime.strptime(time_str, '%m-%d %H:%M')
                            dt = parsed.replace(year=now.year)
                            return dt.replace(tzinfo=kst)
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
    """
    if dt is None:
        return None

    # 이미 문자열인 경우
    if isinstance(dt, str):
        # 이미 'yyyy-MM-dd HH:mm:ss' 형식인지 확인
        if len(dt) == 19 and dt[4] == '-' and dt[10] == ' ':
            return dt

        # ISO8601 형식이면 변환
        if 'T' in dt:
            try:
                parsed = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                kst = timezone(timedelta(hours=9))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=kst)
                else:
                    parsed = parsed.astimezone(kst)
                return parsed.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass

        # 아닌 경우 파싱 후 변환 시도
        parsed = parse_time(dt)
        if parsed:
            dt = parsed
        else:
            return None

        # datetime 객체를 'yyyy-MM-dd HH:mm:ss'로 변환
    kst = timezone(timedelta(hours=9))

    # timezone이 없으면 KST 추가
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=kst)

    # KST로 변환
    if dt.tzinfo != kst:
        dt = dt.astimezone(kst)

    print(f"to_iso8601 return = {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # 'yyyy-MM-dd HH:mm:ss' 형식 반환 (timezone 정보 제거)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

