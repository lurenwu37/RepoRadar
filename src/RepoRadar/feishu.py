import os
import json
import urllib.request
import urllib.error


def get_webhook_urls():
    raw = os.environ.get("FEISHU_WEBHOOK_URLS") or os.environ.get("FEISHU_WEBHOOK_URL") or ""
    return [u.strip() for u in raw.split(",") if u.strip()]


def parse_recommendations(text):
    NL = chr(10)
    items = []
    current = {}
    for line in text.split(NL):
        line = line.strip()
        if not line:
            if current:
                items.append(current)
                current = {}
            continue
        first_two = line[:2] if len(line) >= 2 else ""
        if first_two in ("1.", "2.", "3.", "4.", "5.") and len(line) > 3 and line[2] == " ":
            if current:
                items.append(current)
            current = {"header": line, "body_what": "", "body_use": ""}
        elif "推荐语" in line or "【什么是它】" in line or "【有什么用】" in line:
            content = line
            if "推荐语：" in line:
                content = line.split("推荐语：", 1)[1].strip()
            elif "推荐语:" in line:
                content = line.split("推荐语:", 1)[1].strip()
                
            if "【什么是它】" in content and "【有什么用】" in content:
                part1, part2 = content.split("【有什么用】", 1)
                current["body_what"] = part1.replace("【什么是它】", "").strip()
                current["body_use"] = part2.strip()
            elif "【什么是它】" in content:
                current["body_what"] = content.replace("【什么是它】", "").strip()
            elif "【有什么用】" in content:
                current["body_use"] = content.replace("【有什么用】", "").strip()
            else:
                current["body_what"] = content
        else:
            if "header" in current:
                if "【什么是它】" in line and "【有什么用】" in line:
                    part1, part2 = line.split("【有什么用】", 1)
                    current["body_what"] = part1.replace("【什么是它】", "").strip()
                    current["body_use"] = part2.strip()
                elif "【什么是它】" in line:
                    current["body_what"] = line.replace("【什么是它】", "").strip()
                elif "【有什么用】" in line:
                    current["body_use"] = line.replace("【有什么用】", "").strip()
                else:
                    if not current["body_what"]:
                        current["body_what"] = line
                    else:
                        current["body_use"] += " " + line
    if current:
        items.append(current)
    return items


def build_card_dict(title, recommendations_text, total_fetched, days_back=1):
    elements = []
    
    # 动态头部描述
    if days_back == 30:
        time_desc = "过去 30 天"
        header_desc = "📡 **GitHub 每月明星资讯雷达（抓取过去 30 天最热开源项目）**"
    elif days_back == 7:
        time_desc = "过去 7 天"
        header_desc = "📡 **GitHub 每周明星资讯雷达（抓取过去 7 天最热开源项目）**"
    else:
        time_desc = "昨日"
        header_desc = "📡 **GitHub 每日明星资讯雷达（抓取昨日最热开源项目）**"

    header_content = (
        f"{header_desc}" + chr(10) +
        f"{time_desc}共抓取评估了 **{total_fetched}** 个高热新项目，以下是为您智能精选的 **5 个最强推荐**："
    )
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": header_content
        }
    })
    elements.append({"tag": "hr"})

    items = parse_recommendations(recommendations_text)
    
    if items:
        for i, item in enumerate(items[:5], 1):
            header = item.get("header", "").strip()
            body_what = item.get("body_what", "").strip()
            body_use = item.get("body_use", "").strip()
            
            emojis = ["①", "②", "③", "④", "⑤"]
            num_emoji = emojis[i-1] if i <= len(emojis) else "⭐"
            
            clean_header = header
            if header[:2] in ("1.", "2.", "3.", "4.", "5."):
                clean_header = header[2:].strip()
                
            formatted_content = (
                f"**{num_emoji} {clean_header}**" + chr(10) +
                f"🎯 **这东西是什么**：" + chr(10) +
                f"{body_what if body_what else '开源技术项目库'}" + chr(10) +
                f"🛠️ **有什么用（场景）**：" + chr(10) +
                f"{body_use if body_use else '提供了创新的开发者工具和高效的实用解决方案。'}"
            )
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": formatted_content
                }
            })
            if i < 5:
                elements.append({"tag": "hr"})
    else:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": recommendations_text
            }
        })

    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"📊 数据源: GitHub Trending ({time_desc}新增 Star 排序) | 由 Agnes 智能打分、技术定位总结"
            }
        ]
    })

    card = {
        "config": {
            "wide_screen_mode": True,
            "enable_forward": True
        },
        "header": {
            "template": "blue",
            "title": {
                "tag": "plain_text",
                "content": title
            }
        },
        "elements": elements
    }
    return card


def send_to_one_webhook(webhook_url, title, recommendations_text, total_count, days_back=1):
    card_dict = build_card_dict(title, recommendations_text, total_count, days_back)
    card_str = json.dumps(card_dict, ensure_ascii=False)

    payload = {
        "msg_type": "interactive",
        "card": card_str
    }

    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=body_bytes,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode("utf-8")
            resp = json.loads(res_body)
            code = resp.get("code", -1)
            if code != 0:
                raise Exception(f"Feishu code={code} msg={resp.get('msg')} raw={res_body}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e else ""
        raise Exception(f"HTTPError {e.code}: {err_body}")


def send_to_feishu(title, recommendations_text, total_count=30, days_back=1):
    urls = get_webhook_urls()
    if not urls:
        print("[Feishu] FEISHU_WEBHOOK_URL not configured — printing to console:")
        print("=" * 60)
        print("Title:", title)
        print(recommendations_text)
        print("=" * 60)
        return
    print(f"[Feishu] Sending interactive message card to {len(urls)} webhook(s)...")
    for url in urls:
        try:
            send_to_one_webhook(url, title, recommendations_text, total_count, days_back)
            print("  [Feishu] ✓ Card sent successfully!")
        except Exception as e:
            print("  [Feishu] ✗ Send failed:", e)
            raise e
