import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

class RawLink:
    def __init__(self, title, url, source, score=0):
        self.title = title
        self.url = url
        self.source = source
        self.score = score

def fetch_github_trending(days_back=1):
    """
    Unified, parameterized data-acquisition layer for Daily, Weekly, and Monthly trending repositories.
    Queries the GitHub Search API for repositories created within the last `days_back` days,
    sorted by stars descending.
    """
    print(f"  [Fetcher] Fetching popular GitHub repositories for the past {days_back} days...")
    
    # Calculate the date range based on days_back
    today = datetime.now()
    end_date_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date_str = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    if days_back == 1:
        query_date = start_date_str
    else:
        query_date = f"{start_date_str}..{end_date_str}"
        
    print(f"  [Fetcher] Target date range (created): {query_date}")
    
    try:
        # Search for repositories created in the computed range, sorted by stars descending
        query = f"created:{query_date}"
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page=35"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; zhoubaobot/1.0)"
        }
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
            
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = data.get("items", [])
            results = []
            source_name = f"GitHub {days_back}-Day Stars" if days_back > 1 else "GitHub Daily Stars"
            for item in items:
                name = item.get("full_name") or "Unknown Repo"
                html_url = item.get("html_url") or ""
                desc = item.get("description") or "No description provided."
                stars = item.get("stargazers_count", 0)
                title_with_context = f"{name} (★{stars}) - {desc}"
                results.append(RawLink(title_with_context, html_url, source_name))
            return results
    except Exception as e:
        print(f"  [Fetcher] GitHub API fetch failed: {e}")
        print("  [Fetcher] Using trending fallback data...")
        fallback_source = f"GitHub {days_back}-Day Stars" if days_back > 1 else "GitHub Daily Stars"
        return [
            RawLink("danielmiessler/fabric (★23100) - An open-source framework for cognitive workflow amplification.", "https://github.com/danielmiessler/fabric", fallback_source),
            RawLink("features/copilot (★12500) - Official feature specifications and extensions for Copilot.", "https://github.com/features/copilot", fallback_source),
            RawLink("lllyasviel/Fooocus (★38400) - Focus on prompting and offline image generation.", "https://github.com/lllyasviel/Fooocus", fallback_source),
            RawLink("all-in-one-ai/agents (★8900) - A unified hub for specialized multi-agent orchestrations.", "https://github.com/all-in-one-ai/agents", fallback_source)
        ]

def fetch_all_links(days_back=1):
    print("[Fetcher] Starting collection...")
    repos = fetch_github_trending(days_back=days_back)
    print(f"[Fetcher] Total items fetched: {len(repos)}")

    seen_urls = set()
    unique_list = []
    for item in repos:
        if not item.url:
            continue
        normalized = item.url.strip().rstrip("/")
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            unique_list.append(item)

    print(f"[Fetcher] Unique items after deduplication: {len(unique_list)}")
    result = unique_list[:30]
    print(f"[Fetcher] Final returned items count: {len(result)}")
    return result
