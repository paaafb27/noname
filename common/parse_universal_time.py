def _parse_universal_time(time_text):
    """
    [v2] 다양한 형태의 시간 문자열을 파싱하여 timezone-aware datetime 객체로 변환합니다.
    - "MM-DD" 형식을 지원합니다. (올해 연도 자동 추가)
    """
    import re
    from datetime import datetime, timezone, timedelta

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    time_text = time_text.strip()

    try:
        # ISO 8601 형식 (가장 정확)
        if 'T' in time_text:
            if time_text.endswith('Z'):
                time_text = time_text[:-1] + '+00:00'
            return datetime.fromisoformat(time_text)

        # "N분 전" / "N시간 전" / "방금" 형식
        if '분 전' in time_text:
            return now - timedelta(minutes=int(re.search(r'(\d+)', time_text).group(1)))
        if '시간 전' in time_text:
            return now - timedelta(hours=int(re.search(r'(\d+)', time_text).group(1)))
        if '방금' in time_text:
            return now

        # "HH:mm" 또는 "HH:mm:ss" 형식 (오늘 날짜)
        if ':' in time_text and '-' not in time_text and '.' not in time_text and '/' not in time_text:
            parts = list(map(int, time_text.split(':')))
            return now.replace(hour=parts[0], minute=parts[1], second=parts[2] if len(parts) > 2 else 0, microsecond=0)

        # "YYYY-MM-DD" 또는 "YY-MM-DD" 또는 "MM-DD" 형식 (★★★★★ v2 변경점 ★★★★★)
        if '-' in time_text:
            parts = time_text.split('-')
            if len(parts) == 3:  # YYYY-MM-DD 또는 YY-MM-DD
                return datetime.strptime(time_text, '%Y-%m-%d' if len(parts[0]) == 4 else '%y-%m-%d').replace(
                    tzinfo=kst)
            elif len(parts) == 2:  # MM-DD
                # 올해 연도를 붙여서 완전한 날짜로 만듦
                return datetime.strptime(f"{now.year}-{time_text}", '%Y-%m-%d').replace(tzinfo=kst)

        # "YYYY.MM.DD" 또는 "YY.MM.DD" 형식
        if '.' in time_text:
            return datetime.strptime(time_text,
                                     '%Y.%m.%d' if len(time_text.split('.')[0]) == 4 else '%y.%m.%d').replace(
                tzinfo=kst)

        return None
    except Exception as e:
        print(f"  [PARSING-ERROR] 범용 시간 파싱 실패: '{time_text}', 오류: {e}")
        return None


#
