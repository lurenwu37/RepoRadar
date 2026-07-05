import os
import sys
import datetime


def load_dotenv():
    """
    Zero-dependency .env loader.
    Searches for .env in the zhoubaobot directory, its parent, and grandparent.
    """
    current = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(current, ".env"),
        os.path.join(current, "..", ".env"),
        os.path.join(current, "..", "..", ".env"),
    ]
    for path in candidates:
        path = os.path.normpath(path)
        if os.path.isfile(path):
            print(f"[Env] Loading .env from: {path}")
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:  # don't override already-set vars
                        os.environ[key] = val
            return path
    print("[Env] No .env file found — using system environment variables only.")
    return None


def main():
    # Force UTF-8 stdout on Windows
    if hasattr(sys.stdout, "buffer"):
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Auto-load .env FIRST, before importing any modules that read env vars
    load_dotenv()

    # Import after env is loaded
    from fetcher import fetch_all_links
    from scorer import score_and_recommend
    from feishu import send_to_feishu

    print("=" * 60)
    print("  Zhoubao Bot — AI Monthly Report")
    print("=" * 60)

    # 1. Fetch 30 unique links for the past 30 days
    links = fetch_all_links(days_back=30)

    # 2. Score and generate top-5 recommendations via LLM
    scored_links, recommendations = score_and_recommend(links)

    # 3. Send beautiful card to Feishu
    today = datetime.date.today()
    # Calculate start date of the month (30 days ago)
    start_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    title = f"📡 GitHub 月度明星雷达 ({start_date} ~ {end_date})"

    send_to_feishu(title, recommendations, total_count=len(links), days_back=30)

    print("=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()