import requests
import json
import base64
import time
import re
from datetime import datetime

# ===== 配置 =====
SITE_URL = "https://m.360ba.co/"
API_URL = "https://m.360ba.co/api/web/live_lists/3?&supplement=0"
REFERER = "https://www.360ba.co/"
USER_AGENT = "Mozilla/5.0 (Linux; Android 12; Redmi K30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36"

HEADERS = {
  "User-Agent": "Mozilla/5.0 (Linux; Android 12; Redmi K30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36",
    "Referer": "https://m.360ba.co/",
    "Origin": "https://m.360ba.co",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}

OUTPUT_FILE = "basketball.m3u"

def get_basketball_matches():
    """获取所有篮球比赛列表"""
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=10)
        print("=== 响应状态码 ===")
        print(resp.status_code)
        print("=== 响应内容（前500字符）===")
        print(resp.text[:500])
        data = resp.json()
        print(data)
        return data.get("data", {}).get("data", [])
    except Exception as e:
        print(f"[ERROR] 获取比赛列表失败: {e}")
        return []

def generate_token(stream_id):
    """生成 token（模拟 JS 的 btoa + 替换）"""
    end_time = int(time.time()) + 30
    payload = f'{{"stream_id":"{stream_id}","end_time":{end_time}}}'
    token = base64.b64encode(payload.encode()).decode()
    token = token.replace("+", "-").replace("/", "-")
    return token

def get_play_url(match):
    """获取单个比赛的真实 m3u8 地址"""
    tid = match["type"]
    tournament_id = match["tournament_id"]
    member_id = match["member_id"]
    
    detail_url = f"https://www.360ba.co/api/web/live_lists/{tid}/detail/{tournament_id}?member_id={member_id}"
    
    try:
        resp = requests.get(detail_url, headers=HEADERS, timeout=10)
        data = resp.json()
        raw_url = data["data"]["detail"]["url"]
        
        # 提取 stream_id
        match_obj = re.search(r'live/(.*?)\.', raw_url)
        if not match_obj:
            return None
        stream_id = match_obj.group(1)
        
        token = generate_token(stream_id)
        final_url = f"{raw_url}&token={token}"
        return final_url
    except Exception as e:
        print(f"[ERROR] 获取 {match['home_team_zh']} vs {match['away_team_zh']} 失败: {e}")
        return None

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始采集篮球直播...")
    matches = get_basketball_matches()
    print(f"找到 {len(matches)} 场篮球比赛")

    m3u_lines = ["#EXTM3U"]
    for match in matches:
        name = f"{match['league_name_zh']} {match['home_team_zh']} VS {match['away_team_zh']}"
        play_url = get_play_url(match)
        if play_url:
            m3u_lines.append(f'#EXTINF:-1,{name}')
            m3u_lines.append(play_url)
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - 无法获取流")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    print(f"✅ M3U 文件已生成: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
