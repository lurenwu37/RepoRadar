import os
import sys
import json
import urllib.request
import urllib.parse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from report import call_llm
except ImportError:
    def call_llm(prompt, max_tokens=4096):
        api_key = os.environ.get("AGNES_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("AGNES_API_BASE") or os.environ.get("OPENAI_API_BASE") or "https://api.deepseek.com/v1"
        
        if not api_key:
            raise ValueError("No API Key configured (AGNES_API_KEY, DEEPSEEK_API_KEY or OPENAI_API_KEY is missing)")
            
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        model = os.environ.get("AGNES_MODEL") or os.environ.get("LLM_MODEL") or "deepseek-chat"
        req_body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": max_tokens
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(req_body).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]

def score_and_recommend(links):
    print(f"[Scorer] Scoring {len(links)} links using LLM...")
    if not links:
        return [], "No links fetched today."

    formatted_items = []
    for idx, item in enumerate(links):
        clean_title = item.title.replace('"', '')
        formatted_items.append(f"[{idx}] Title: {clean_title} | Source: {item.source} | URL: {item.url}")
    
    links_text = "\n".join(formatted_items)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "prompt.txt")
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
    except Exception as e:
        print(f"[Scorer] Failed to read prompt.txt: {e}. Falling back to default template.")
        template = "Please score these links: {links_list_placeholder}"

    prompt = template.replace("{link_count}", str(len(links))).replace("{links_list_placeholder}", links_text)

    try:
        response = call_llm(prompt)
        clean_json = response.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_json)

        scored_links = []
        scores_map = {item["index"]: item["score"] for item in parsed.get("scores", [])}
        
        for idx, item in enumerate(links):
            score = scores_map.get(idx, 50)
            item.score = score
            scored_links.append(item)

        scored_links.sort(key=lambda x: x.score, reverse=True)
        return scored_links, parsed.get("recommendations", "")

    except Exception as err:
        print(f"[Scorer] LLM scoring failed: {err}. Falling back to rule-based scoring.")
        scored_links = []
        for item in links:
            score = 50
            lower_title = item.title.lower()
            if "agent" in lower_title or "model" in lower_title or "ai" in lower_title or "llm" in lower_title:
                score += 35
            item.score = score
            scored_links.append(item)
            
        scored_links.sort(key=lambda x: x.score, reverse=True)
        top5 = scored_links[:5]
        
        recommendations = ""
        for i, item in enumerate(top5):
            recommendations += f"{i+1}. **[{item.title}]({item.url})** (得分: {item.score})\n"
            recommendations += (
    "推荐语：【什么是它】这是一个GitHub每日明星开源项目。\n"
    "【有什么用】提供极高生产力和开发者效能，代表昨日最受社区瞩目的开源突破。\n\n"
)
            
        return scored_links, recommendations
