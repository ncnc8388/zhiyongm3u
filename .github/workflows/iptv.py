import os
import aiohttp
import asyncio
import time
from collections import defaultdict
import re
from datetime import datetime, timedelta


def get_dynamic_keywords():
    """
    动态生成需要过滤的关键词（今天的日期、明天的日期以及固定关键词）
    """
    fixed_keywords = ["免费提供"]
    return fixed_keywords

def contains_date(text):
    """
    检测字符串中是否包含日期格式（如 YYYY-MM-DD）
    """
    date_pattern = r"\d{4}-\d{2}-\d{2}"  # 正则表达式匹配 YYYY-MM-DD
    return re.search(date_pattern, text) is not None


# 配置
CONFIG = {
    "timeout": 10,  # Timeout in seconds
    "max_parallel": 30,  # Max concurrent requests
    "output_file": "best_sorted.m3u",  # Output file for the sorted M3U
    "iptv_directory": "IPTV"  # Directory containing IPTV files
}


# 读取 CCTV 频道列表
def load_cctv_channels(file_path=".github/workflows/IPTV/CCTV.txt"):
    """从文件加载 CCTV 频道列表"""
    cctv_channels = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:  # Ignore empty lines
                    cctv_channels.add(line)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    return cctv_channels


# 读取 IPTV 目录下所有省份频道文件
def load_province_channels(directory="IPTV"):
    """加载所有省份的频道列表"""
    province_channels = defaultdict(set)

    for filename in os.listdir(directory):
        if filename.endswith(".txt") and filename != "CCTV.txt":  # 排除 CCTV.txt 文件
            province_name = filename.replace(".txt", "")  # 使用文件名作为省份名称
            file_path = os.path.join(directory, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line:  # Ignore empty lines
                            province_channels[province_name].add(line)
            except FileNotFoundError:
                print(f"Error: The file {file_path} was not found.")

    return province_channels


# 正规化 CCTV 频道名称
def normalize_cctv_name(channel_name):
    """将 CCTV 频道名称进行正规化，例如 CCTV-1 -> CCTV1"""
    return re.sub(r'CCTV[-]?(\d+)(.*)', r'CCTV\1', channel_name.strip())


# 从 TXT 文件中提取 IPTV 链接
def extract_urls_from_txt(content,ppp):
    """从 TXT 文件中提取 IPTV 链接"""
    urls = []
    gzc = ["凤凰", "咪咕视频", "睛彩","鳳凰","日","中天","咪视界"]
    for line in content.splitlines():
        line = line.strip()
        if line and ',' in line:  # 格式应该是: <频道名>,<URL>
            parts = line.split(',', 1)
            if ppp =='河南':
                urls.append(parts)  # 提取频道名和 URL
            else:
                if any(gzcy in line for gzcy in gzc):
                    urls.append(parts)  # 提取频道名和 URL

    return urls


# 从 M3U 文件中提取 IPTV 链接
def extract_urls_from_m3u(content,ppp):
    """从 M3U 文件中提取 IPTV 链接"""
    urls = []
    lines = content.splitlines()
    channel = "Unknown"
    gzc = ["凤凰", "咪咕视频", "睛彩","鳳凰","日","中天","咪视界"]
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # 从 EXTINF 标签中提取频道名
            parts = line.split(',', 1)
            channel = parts[1] if len(parts) > 1 else "Unknown"
        elif line.startswith(('http://', 'https://')):
            if ppp =='河南':
                urls.append((channel, line))  # 存
            elif  any(gzcy in channel for gzcy in gzc):
                urls.append((channel, line))  # 存储频道和 URL 的元组
    return urls


# 测试 IPTV 链接的可用性和速度
async def test_stream(url):
    """测试 IPTV 链接的可用性和速度"""
    async with aiohttp.ClientSession(cookie_jar=None) as session:  # 禁用 cookie 处理
        start_time = time.time()
        try:
            async with session.get(url, timeout=CONFIG["timeout"]) as response:
                if response.status == 200:
                    # 计算响应时间
                    elapsed_time = time.time() - start_time
                    return True, elapsed_time
                else:
                    return False, None
        except asyncio.TimeoutError:
            return False, None
        except Exception as e:
            return False, None


# 测试多个 IPTV 链接
async def test_multiple_streams(urls):
    """测试多个 IPTV 链接"""
    tasks = [test_stream(url) for _, url in urls]
    results = await asyncio.gather(*tasks)
    return results


# 读取文件并提取 URL（支持 M3U 或 TXT 格式）
async def read_and_test_file(file_path, is_m3u=False):
    """读取文件并提取 URL 进行测试"""
    try:
        # 获取文件内容
        async with aiohttp.ClientSession(cookie_jar=None) as session:  # 禁用 cookie 处理
            async with session.get(file_path) as response:
                content = await response.text()
        print(content)
        # 提取 URL
        if is_m3u:
            if '河南' in file_path:
                entries = extract_urls_from_m3u(content,'河南')
            else:
                entries = extract_urls_from_m3u(content,'aaa')
        else:
            if '河南' in file_path:
                entries = extract_urls_from_txt(content,'河南')
            else:
                entries = extract_urls_from_txt(content,'aaa')

        # 测试 URL 的可用性
        valid_urls = []
        print(entries)
       # results = await test_multiple_streams(entries)
       # for (is_valid, _), (channel, url) in zip(results, entries):
          #  if is_valid:
        for (channel, url) in entries :
                valid_urls.append((channel, url))

        return valid_urls

    except Exception as e:
        return []


# 生成排序后的 M3U 文件

def generate_sorted_m3u(valid_urls, cctv_channels, province_channels, filename):
    """生成排序后的 M3U 文件"""
    cctv_channels_list = []
    province_channels_list = defaultdict(list)
    satellite_channels = []
    other_channels = []
    keywords = get_dynamic_keywords()
    #print(valid_urls)
    for channel, url in valid_urls:
        print(channel)
        if contains_date(channel) or contains_date(url):
            continue  # 过滤掉包含日期格式的频道
        # 正规化 CCTV 频道名
        normalized_channel = normalize_cctv_name(channel)

        # 根据频道名判断属于哪个分组
        if normalized_channel in cctv_channels:
            cctv_channels_list.append({
                "channel": channel,
                "url": url,
                "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                "group_title": "央视频道"
            })
        elif "卫视" in channel:  # 卫视频道
            satellite_channels.append({
                "channel": channel,
                "url": url,
                "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                "group_title": "卫视频道"
            })
        elif "凤凰" in channel:  # 卫视频道
            satellite_channels.append({
                "channel": channel,
                "url": url,
                "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                "group_title": "港澳频道"
            })
        else:
            # 检查是否是省份频道
            print(province_channels)
            found_province = False
            for province, channels in province_channels.items():
                for province_channel in channels:
                    print(province_channel)
                    if province_channel in channel:  # 匹配省份频道名称
                        province_channels_list[province].append({
                            "channel": channel,
                            "url": url,
                            "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                            "group_title": f"{province}"
                        })
                        found_province = True
                        break
                if found_province:
                    break
            print(province_channels_list)     
            """if not found_province:
                other_channels.append({
                    "channel": channel,
                    "url": url,
                    "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                    "group_title": "其他频道"
                })"""

    # 排序：省份频道、卫视频道、其他频道
    for province in province_channels_list:
        province_channels_list[province].sort(key=lambda x: x["channel"])

    satellite_channels.sort(key=lambda x: x["channel"])
    #other_channels.sort(key=lambda x: x["channel"])

    # 合并所有频道：CCTV -> 卫视频道 -> 省份频道 -> 其他
    all_channels = (cctv_channels_list + satellite_channels +
                   [channel for province in sorted(province_channels_list) for channel in
                    province_channels_list[province]])
                 #   + \other_channels)

    # 写入 M3U 文件
    with open(filename, 'w', encoding='utf-8') as f:
       # for urlxx in valid_urls:
          #  f.write(str(urlxx) + '\n')
        f.write("#EXTM3U\n")
        for channel_info in all_channels:
            f.write(
                f"#EXTINF:-1 tvg-name=\"{channel_info['channel']}\" tvg-logo=\"{channel_info['logo']}\" group-title=\"{channel_info['group_title']}\",{channel_info['channel']}\n")
            f.write(f"{channel_info['url']}\n")



# 加载省份频道列表
def load_province_channels(files):
    """加载多个省份的频道列表"""
    province_channels = defaultdict(set)

    for file_path in files:
        province_name = os.path.basename(file_path).replace(".txt", "")  # 使用文件名作为省份名称

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:  # 忽略空行
                        province_channels[province_name].add(line)
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")

    return province_channels


# 主函数：处理多个文件并生成 M3U 输出
async def main(file_urls, cctv_channel_file, province_channel_files):
    """主函数处理多个文件"""
    # 加载 CCTV 频道列表
    cctv_channels = load_cctv_channels(cctv_channel_file)

    # 加载多个省份频道列表
    province_channels = load_province_channels(province_channel_files)

    all_valid_urls = []

    for file_url in file_urls:
        if file_url.endswith(('.m3u', '.m3u8')):
            valid_urls = await read_and_test_file(file_url, is_m3u=True)
        elif file_url.endswith(('.txt','.nzk')):
            valid_urls = await read_and_test_file(file_url, is_m3u=False)
        else:
            valid_urls = await read_and_test_file(file_url, is_m3u=True)

        all_valid_urls.extend(valid_urls)

    # 生成排序后的 M3U 文件
    generate_sorted_m3u(all_valid_urls, cctv_channels, province_channels, CONFIG["output_file"])
    print(f"🎉 Generated sorted M3U file: {CONFIG['output_file']}")

if __name__ == "__main__":
    # IPTV 文件 URL（您可以添加自己的文件 URL 列表）
    file_urls = [
        #"https://mp.leuse.top/proxy?single=true&url=https://fy.188766.xyz/?ip=&lunbo=false&mima=mianfeidehaimaiqian",
       # "https://aktv.space/live.m3u",
        #"https://ncncha.3vdo.club/getm3u8.asp?url=https://fy.188766.xyz/?ip=&lunbo=false&mima=mianfeidehaimaiqian",
        "https://gist.githubusercontent.com/ncnc8388/fd7fe346617db3b5d609c806d3a1bc35/raw/live.m3u",
        #"https://1303157606-jbnue8hg1f.ap-guangzhou.tencentscf.com/?url=https://fy.188766.xyz/?ip=&lunbo=false&mima=mianfeidehaimaiqian&haiwai=false",
        #"https://raw.githubusercontent.com/ncnc8388/genxinxia/refs/heads/main/fg.m3u",
        "https://raw.githubusercontent.com/ncnc8388/ncnc8388.github.io/refs/heads/main/河南电信.m3u",
        "https://raw.githubusercontent.com/ncnc8388/zhiyongm3u/refs/heads/main/%E6%B2%B3%E5%8D%97%E7%A7%BB%E5%8A%A8.txt",
        #"https://raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.m3u",
        #"https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/组播_四川电信.txt",
        #"https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/组播_浙江电信.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/组播_山西电信.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/组播_河北电信.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/组播_甘肃电信.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/组播_湖南电信.txt",
        "https://raw.githubusercontent.com/wokaotianshi123/zubotv/refs/heads/main/sichuanzubo.txt",
        #"https://raw.githubusercontent.com/kakaxi-1/zubo/refs/heads/main/itvlist.txt",
       "https://raw.githubusercontent.com/lisa3456/zubo/refs/heads/main/IPTV.txt",
        #"https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/组播_福建电信.txt",
        #"https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/组播_河南电信.txt",
        "https://raw.githubusercontent.com/ncnc8388/zhiyongm3u/refs/heads/main/.github/workflows/IPTV/ITV.txt",
        "https://raw.githubusercontent.com/ncnc8388/zhiyongm3u/refs/heads/main/IPTV/河南yut.m3u",
        "http://rihou.cc:555/gggg.nzk",
        #"https://tzdr.com/iptv.txt",
        #"https://live.kilvn.com/iptv.m3u",
        #"https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.m3u",
        #"https://gh-proxy.com/raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.m3u",
        #"http://175.178.251.183:6689/live.m3u",

       # "https://m3u.ibert.me/ycl_iptv.m3u"
    ]
    #aktv_url = f"http://cgzfxxqg.dynv6.net:8087/aa.m3u?t={int(time.time())}"
    #file_urls = base_urls + [aktv_url]
    print(file_urls)
    # CCTV 频道文件（例如 IPTV/CCTV.txt）
    cctv_channel_file = ".github/workflows/IPTV/CCTV.txt"

    # 省份频道文件列表
    province_channel_files = [
        ".github/workflows/IPTV/河南频道.txt",
        ".github/workflows/IPTV/youtube.txt",
        ".github/workflows/IPTV/冰茶体育.txt"
    ]

    # 执行主函数

    asyncio.run(main(file_urls, cctv_channel_file, province_channel_files))





























































