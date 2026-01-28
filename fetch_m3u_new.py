# fetch_youtube_m3u.py
import os
import requests

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNELS_INPUT = os.getenv("YOUTUBE_CHANNELS", "").strip()

OUTPUT_DIR = "IPTV"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "河南yut.m3u")

def resolve_to_channel_ids(raw_input):
    if not raw_input:
        return []
    items = [s.strip() for s in raw_input.replace('\n', ',').split(',') if s.strip()]
    seen = set()
    channel_ids = []
    for item in items:
        if item.startswith('@'):
            handle = item[1:]
            try:
                resp = requests.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "id", "forHandle": handle, "key": API_KEY},
                    timeout=10
                )
                data = resp.json()
                if data.get("items"):
                    cid = data["items"][0]["id"]
                    if cid not in seen:
                        seen.add(cid)
                        channel_ids.append(cid)
                        print(f"Resolved @{handle} → {cid}")
                else:
                    print(f"⚠️ Handle @{handle} not found")
            except Exception as e:
                print(f"❌ Resolve error for @{handle}: {e}")
        elif item.startswith('UC') and len(item) >= 20:
            if item not in seen:
                seen.add(item)
                channel_ids.append(item)
        else:
            print(f"⚠️ Invalid input: {item}")
    return channel_ids

def get_live_and_videos(channel_ids, max_videos_per_channel=6):
    entries = []  # each: (video_id, title, media_type)

    for cid in channel_ids:
        # === 1. Check Live Stream ===
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
            data = resp.json()
            if data.get("items"):
                item = data["items"][0]
                vid = item["id"]["videoId"]
                title = item["snippet"]["title"].replace("\n", " ").replace(",", " ")
                entries.append((vid, f"[LIVE] {title}", "live"))
        except Exception as e:
            print(f"Live check failed for {cid}: {e}")

        # === 2. Get Latest VOD Videos ===
        try:
            # Get uploads playlist ID
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "contentDetails", "id": cid, "key": API_KEY}
            )
            data = resp.json()
            if not data.get("items"):
                continue
            uploads_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # Fetch latest videos
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                params={
                    "part": "snippet",
                    "playlistId": uploads_id,
                    "maxResults": max_videos_per_channel,
                    "order": "date",
                    "key": API_KEY
                }
            )
            data = resp.json()
            for item in data.get("items", []):
                vid = item["snippet"]["resourceId"]["videoId"]
                title = item["snippet"]["title"].replace("\n", " ").replace(",", " ")
                entries.append((vid, f"[VOD] {title}", "vod"))
        except Exception as e:
            print(f"Video fetch failed for {cid}: {e}")

    return entries

def write_m3u(entries):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    BASE_URL = "http://ncncha.cloudns.ch:9977/play"
    lines = ["#EXTM3U"]
    
    for vid, title, media_type in entries:
        if media_type == "live":
            url = f"{BASE_URL}?id={vid}&quality=360p"
        else:  # vod
            url = f"{BASE_URL}?id={vid}&quality=720p"
        lines.append(f'#EXTINF:-1,youtube {title}')
        lines.append(url)
    
    content = "\n".join(lines) + "\n" if entries else "#EXTM3U\n# No content available\n"
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Written {len(entries)} entries to {OUTPUT_FILE}")

if __name__ == "__main__":
    if not API_KEY:
        raise ValueError("❌ YOUTUBE_API_KEY is not set")
    if not CHANNELS_INPUT:
        raise ValueError("❌ YOUTUBE_CHANNELS is empty")

    channel_ids = resolve_to_channel_ids(CHANNELS_INPUT)
    if not channel_ids:
        print("⚠️ No valid channels resolved")
        write_m3u([])
    else:
        entries = get_live_and_videos(channel_ids, max_videos_per_channel=6)
        write_m3u(entries)
