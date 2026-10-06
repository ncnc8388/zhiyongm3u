import sys
import os

# 🔥 核心修复：强制 GitHub Actions 环境使用 UTF-8 编码，防止中文引发 ASCII 报错
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import json
import urllib.request
import urllib.error
import urllib.parse

def main():
    # 1. 拆分 URL 并进行显式的 URL 编码
    base_url1 = "https://raw.githubusercontent.com/FGBLH/EHR663/refs/heads/main/"
    filename1 = "ok海豚常规996"
    # quote 会将中文安全地转换为 %E6%B5%B7... 格式
    url1 = base_url1 + urllib.parse.quote(filename1)
    
    url2 = "https://raw.githubusercontent.com/ncnc8388/ncnc8388.github.io/refs/heads/main/py.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'application/vnd.github.v3.raw',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    def fetch_json(url, name):
        # 使用 encode('utf-8') 确保 print 不会触发 ascii 错误
        print(f"Fetching {name}: {url}".encode('utf-8').decode('utf-8'))
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                status = response.status
                print(f"   -> HTTP Status: {status}")
                
                raw_bytes = response.read()
                raw_text = raw_bytes.decode('utf-8')
                
                if status != 200:
                    print(f"ERROR: {name} failed. Raw response:\n{raw_text[:500]}")
                    return None
                
                try:
                    data = json.loads(raw_text)
                    print(f"   SUCCESS: {name} JSON parsed.")
                    return data
                except json.JSONDecodeError as e:
                    print(f"ERROR: {name} is not valid JSON. Error: {e}")
                    print(f"   Raw content preview:\n{raw_text[:300]}")
                    return None
                    
        except urllib.error.URLError as e:
            print(f"ERROR: {name} network request failed: {e}")
            return None
        except Exception as e:
            print(f"ERROR: {name} unknown error: {e}")
            return None

    data1 = fetch_json(url1, "URL1")
    data2 = fetch_json(url2, "URL2")
    
    if data1 is None or data2 is None:
        print("Terminating: Failed to fetch data. Check logs above.")
        sys.exit(1)
        
    list1 = data1.get('sites', data1.get('site', []))
    list2 = data2.get('sites', data2.get('site', []))
    
    if not isinstance(list1, list): list1 = []
    if not isinstance(list2, list): list2 = []
    
    merged_list = list2 + list1
    print(f"SUCCESS: Merged {len(merged_list)} sites.")
    
    if 'sites' in data1:
        data1['sites'] = merged_list
    elif 'site' in data1:
        data1['site'] = merged_list
    else:
        data1['sites'] = merged_list
        
    output_file = "merged_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data1, f, indent=2, ensure_ascii=False)
        
    print(f"SUCCESS: Saved to {output_file}")

if __name__ == "__main__":
    main()
