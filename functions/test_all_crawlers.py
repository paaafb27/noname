# test_all_crawlers.py
import subprocess
import sys

crawlers = [
    'ppomppu',
    'ruliweb',
    'fmkorea',
    'quasarzone',
    'arcalive',
    'eomisae'
]


def test_crawler(crawler_name):
    """개별 크롤러 테스트"""
    print(f"\n{'=' * 50}")
    print(f"🧪 테스트: {crawler_name}")
    print(f"{'=' * 50}")

    try:
        result = subprocess.run(
            [sys.executable, f'{crawler_name}/scraper.py'],
            capture_output=True,
            text=True,
            timeout=60  # 60초 타임아웃
        )

        if result.returncode == 0:
            print(f"✅ {crawler_name}: 성공")
            print(result.stdout[-200:] if len(result.stdout) > 200 else result.stdout)
            return True
        else:
            print(f"❌ {crawler_name}: 실패")
            print(result.stderr[-200:] if len(result.stderr) > 200 else result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"⏱️ {crawler_name}: 타임아웃 (60초 초과)")
        return False
    except Exception as e:
        print(f"❌ {crawler_name}: 에러 - {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 6개 크롤러 자동 테스트 시작\n")

    results = {}
    for crawler in crawlers:
        results[crawler] = test_crawler(crawler)

    print(f"\n{'=' * 50}")
    print("📊 최종 결과")
    print(f"{'=' * 50}")

    success_count = sum(results.values())
    total_count = len(results)

    for crawler, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{crawler}: {status}")

    print(f"\n성공률: {success_count}/{total_count} ({success_count / total_count * 100:.1f}%)")

    if success_count == total_count:
        print("\n🎉 모든 크롤러 정상 작동!")
    else:
        print(f"\n⚠️ {total_count - success_count}개 크롤러 문제 발생")