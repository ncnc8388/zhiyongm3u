import json
import urllib.request
import urllib.error
import sys

def main():
    # 直接使用中文文件名，urllib 会自动进行标准且正确的 URL 编码
    # 请确保你的 GitHub 仓库中文件名确实是 "ok海豚常规996" (无 .json 后缀)
    url1 = "https://raw.githubusercontent.com/FGBLH/EHR663/refs/heads/main/ok海豚常规996"
    url2 = "https://raw.githubusercontent.com/ncnc8388/ncnc8388.github.io/refs/heads/main/py.json"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        print(f"📥 正在获取 URL1: {url1}")
        req1 = urllib.request.Request(url1, headers=headers)
        with urllib.request.urlopen(req1) as response:
            if response.status != 200:
                raise Exception(f"URL1 返回异常状态码: {response.status}")
            raw_text1 = response.read().decode('utf-8')
            
        print(f"📥 正在获取 URL2: {url2}")
        req2 = urllib.request.Request(url2, headers=headers)
        with urllib.request.urlopen(req2) as response:
            if response.status != 200:
                raise Exception(f"URL2 返回异常状态码: {response.status}")
            raw_text2 = response.read().decode('utf-8')
            
        # 尝试解析 JSON，如果失败则打印原始内容以便精准排错
        try:
            data1 = json.loads(raw_text1)
        except json.JSONDecodeError as e:
            print(f"❌ URL1 返回的不是有效的 JSON！服务器实际返回的内容前 300 个字符为:\n{raw_text1[:300]}")
            raise e
            
        try:
            data2 = json.loads(raw_text2)
        except json.JSONDecodeError as e:
            print(f"❌ URL2 返回的不是有效的 JSON！服务器实际返回的内容前 300 个字符为:\n{raw_text2[:300]}")
            raise e
            
        # 兼容 'sites' 或 'site' 键名
        list1 = data1.get('sites', data1.get('site', []))
        list2 = data2.get('sites', data2.get('site', []))
        
        if not isinstance(list1, list): list1 = []
        if not isinstance(list2, list): list2 = []
        
        # 核心逻辑：将 list2 的内容添加到 list1 的前面
        merged_list = list2 + list1
        print(f"✅ 成功合并，共 {len(merged_list)} 个站点。")
        
        if 'sites' in data1:
            data1['sites'] = merged_list
        elif 'site' in data1:
            data1['site'] = merged_list
        else:
            data1['sites'] = merged_list
            
        output_file = "merged_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data1, f, indent=2, ensure_ascii=False)
            
        print(f"✅ 成功保存至 {output_file}")
        
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 请求被拒绝: {e.code} {e.reason}")
        print(f"服务器返回信息: {e.read().decode('utf-8')[:300]}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
