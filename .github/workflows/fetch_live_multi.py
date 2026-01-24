# fetch_live_multi.py
import os
import requests

API_KEY = os.getenv("YOUTUBE_API_KEY")
# 支持两种格式（自动识别）：
# - @tvbstalk,@channel2   （带 @ 的 handle）
# - UC123,UC456           （直接 channelId）
RAW_INPUT = os.getenv("YOUTUBE_CHANNELS", "").strip()

OUTPUT_DIR = "IPTV"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "yut.m3u")

def resolve_handles_to_channel_ids(handles_or_ids):
    """将混合输入（@handle 或 UC...）统一转为 channelId 列表"""
    channel_ids = []
    for item in handles_or_ids:
        item = item.strip()
        if not item:
            continue
        if item.startswith('@'):
            # 通过 handle 查询 channelId
            handle = item[1:]  # 去掉 @
            try:
                resp = requests.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={
                        "part": "id",
                        "forHandle": handle,
                        "key": API_KEY
                    },
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("items"):
                    cid = data["items"][0]["id"]
                    print(f"Resolved @{handle} → {cid}")
                    channel_ids.append(cid)
                else:
                    print(f"⚠️ Handle @{handle} not found")
            except Exception as e:
                print(f"❌ Failed to resolve @{handle}: {e}")
        elif item.startswith('UC') and len(item) >= 20:
            # 假设是合法的 channelId
            channel_ids.append(item)
        else:
            print(f"⚠️ Skipping invalid input: {item}")
    return channel_ids

def get_all_live_streams(channel_ids):
    """获取所有频道中正在直播的视频（含标题）"""
    live_streams = []
    for cid in channel_ids:
        try:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "channelId": cid,
                    "eventType": "live",
                    "type": "video",
                    "key": API_KEY,
                    "maxResults": 1
                },
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("items"):
                item = data["items"][0]
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"].strip()
                # 清理标题中的特殊字符（避免 M3U 解析问题）
                title = title.replace("\n", " ").replace(",", " ").replace("|", " ")
                live_streams.append((video_id, title))
                print(f"✅ Live: {title} ({video_id})")
        except Exception as e:
            print(f"❌ Error checking channel {cid}: {e}")
    return live_streams

def write_m3u(live_streams):
    """写入 M3U 文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if live_streams:
        lines = ["#EXTM3U"]
        for vid, title in live_streams:
            lines.append(f'#EXTINF:-1,{title}')
            lines.append(f'http://ncncha.cloudns.ch:9977/play?id={vid}&quality=720p')
        content = "\n".join(lines) + "\n"
    else:
        content = "#EXTM3U\n# No live streams available\n"
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Written {len(live_streams)} live stream(s) to {OUTPUT_FILE}")

if __name__ == "__main__":
    if not API_KEY:
        raise ValueError("❌ YOUTUBE_API_KEY is not set in environment variables")
    if not RAW_INPUT:
        raise ValueError("❌ YOUTUBE_CHANNELS is empty")

    # 分割输入（支持逗号或换行）
    inputs = [s.strip() for s in RAW_INPUT.replace('\n', ',').split(',') if s.strip()]
    print(f"Input channels/handles: {inputs}")

    # 解析为 channelId 列表
    channel_ids = resolve_handles_to_channel_ids(inputs)
    if not channel_ids:
        print("⚠️ No valid channel IDs resolved")
        write_m3u([])  # 写空文件
    else:
        # 获取所有直播
        live_streams = get_all_live_streams(channel_ids)
        write_m3u(live_streams)
