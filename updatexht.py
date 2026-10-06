import json
import urllib.request
import sys

def main():
    # 定义两个 JSON 文件的 URL
    url1 = "https://raw.githubusercontent.com/FGBLH/EHR663/refs/heads/main/ok%E6%B5%B7%E8%B1%9A%E5%B8%B8%E8%A7%84996"
    url2 = "https://raw.githubusercontent.com/ncnc8388/ncnc8388.github.io/refs/heads/main/py.json"
    
    # 设置 User-Agent 避免被 GitHub 拒绝访问 (403)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # 1. 读取第一个 JSON
        req1 = urllib.request.Request(url1, headers=headers)
        with urllib.request.urlopen(req1) as response:
            data1 = json.loads(response.read().decode('utf-8'))
            
        # 2. 读取第二个 JSON
        req2 = urllib.request.Request(url2, headers=headers)
        with urllib.request.urlopen(req2) as response:
            data2 = json.loads(response.read().decode('utf-8'))
            
        # 3. 提取 sites 字段 (兼容 'sites' 或 'site' 键名)
        list1 = data1.get('sites', data1.get('site', []))
        list2 = data2.get('sites', data2.get('site', []))
        
        # 确保提取到的是列表
        if not isinstance(list1, list): list1 = []
        if not isinstance(list2, list): list2 = []
        
        # 4. 核心逻辑：将 list2 的内容添加到 list1 的前面
        merged_list = list2 + list1
        
        # 5. 更新 data1 的对应字段
        if 'sites' in data1:
            data1['sites'] = merged_list
        elif 'site' in data1:
            data1['site'] = merged_list
        else:
            data1['sites'] = merged_list
            
        # 6. 将合并后的结果保存到本地文件 (ensure_ascii=False 保证中文/Emoji正常显示)
        output_file = "merged_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data1, f, indent=2, ensure_ascii=False)
            
        print(f"✅ 成功合并并保存至 {output_file}")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
