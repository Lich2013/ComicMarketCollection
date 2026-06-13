import re
import time
import requests
import urllib3
from urllib.parse import urlparse
from src.db import save_circle, get_existing_circle_ids
from src.config import load_config

# 禁用 urllib3 的 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_HALLS = ["e123", "e456", "e7", "e8", "e78", "s12", "s34", "w12", "w34", "c2", "c1"]
DEFAULT_DAYS = ["Day1", "Day2"]

def extract_twitter_username(twitter_url: str) -> str:
    """从 Twitter URL 提取用户名"""
    if not twitter_url:
        return None
    
    # 移除首尾空格
    twitter_url = twitter_url.strip()
    
    # 如果已经是纯用户名或以 @ 开头
    if re.match(r"^@?[a-zA-Z0-9_]{1,15}$", twitter_url):
        return twitter_url.lstrip("@")
    
    # 解析 URL
    try:
        # 补全协议以防 urlparse 无法解析
        if not twitter_url.startswith("http"):
            twitter_url = "https://" + twitter_url
            
        parsed = urlparse(twitter_url)
        path = parsed.path.strip("/")
        
        # 处理类似于 twitter.com/username/status/123 的情况，只取第一级路径
        parts = path.split("/")
        if parts and parts[0]:
            username = parts[0]
            # 排除一些特殊页面名字
            if username.lower() not in ["home", "explore", "notifications", "messages", "search", "settings", "i", "intent", "share", "hashtag"]:
                return username
    except Exception:
        pass
    
    return None

def get_headers(config: dict) -> dict:
    """构造 WebCatalog 请求所需的 Headers"""
    web_config = config.get("webcatalog", {})
    cookie = web_config.get("cookie", "")
    user_agent = web_config.get("user_agent", "")
    
    return {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7",
        "cache-control": "no-cache",
        "cookie": cookie,
        "dnt": "1",
        "pragma": "no-cache",
        "referer": "https://webcatalog.circle.ms/Map",
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": user_agent,
        "x-requested-with": "XMLHttpRequest"
    }

def fetch_hall_map(day: str, hall: str, headers: dict, retries: int = 3) -> list[int]:
    """拉取指定日期和展馆的摊位 ID 列表，带重试机制"""
    url = f"https://webcatalog.circle.ms/Map/GetMapping2?day={day}&hall={hall}"
    print(f"Fetching Map: {day} - {hall}")
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            if response.status_code != 200:
                print(f"Failed to fetch map for {day} {hall}, HTTP {response.status_code} (Attempt {attempt+1}/{retries})")
                time.sleep(2 ** attempt)
                continue
            
            data = response.json()
            # Mapping2 返回的 JSON 中，每个值包含 wid (即 table_id)
            table_ids = []
            for val in data.values():
                if isinstance(val, dict) and "wid" in val:
                    wid = val["wid"]
                    if wid and wid != 0:
                        table_ids.append(wid)
            
            # 去重并排序
            return sorted(list(set(table_ids)))
        except Exception as e:
            print(f"Error fetching map for {day} {hall} (Attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return []
    return []

def fetch_circle_detail(table_id: int, headers: dict, retries: int = 3) -> dict:
    """拉取并解析单个社团详情，带重试机制"""
    url = f"https://webcatalog.circle.ms/Circle/{table_id}/DetailJson"
    
    for attempt in range(retries):
        try:
            # POST 且无 body
            response = requests.post(url, headers=headers, data=None, timeout=10, verify=False)
            if response.status_code != 200:
                print(f"Failed to fetch circle detail for table_id={table_id}, HTTP {response.status_code} (Attempt {attempt+1}/{retries})")
                if response.status_code == 429:
                    time.sleep(5)
                else:
                    time.sleep(2 ** attempt)
                continue
            
            data = response.json()
            if not data or not data.get("Id"):
                return None
                
            cut_urls = data.get("CircleCutUrls") or []
            circle_cut_url = None
            if cut_urls and cut_urls[0]:
                circle_cut_url = "https://webcatalog.circle.ms" + cut_urls[0]
                
            twitter_url = data.get("TwitterUrl")
            twitter_username = extract_twitter_username(twitter_url)
            
            return {
                "id": data.get("Id"),
                "name": data.get("Name"),
                "author": data.get("Author"),
                "genre": data.get("Genre"),
                "description": data.get("Description"),
                "hall": data.get("Hall"),
                "day": data.get("Day"),
                "block": data.get("Block"),
                "space": data.get("Space"),
                "twitter_url": twitter_url,
                "twitter_username": twitter_username,
                "pixiv_url": data.get("PixivUrl"),
                "circle_cut_url": circle_cut_url
            }
        except Exception as e:
            print(f"Error fetching circle detail for table_id={table_id} (Attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None
    return None


def sync_circles_data(day_list: list[str] = None, hall_list: list[str] = None, db_path: str = None, force: bool = False):
    """同步社团数据的总入口"""
    day_list = day_list or DEFAULT_DAYS
    hall_list = hall_list or DEFAULT_HALLS
    
    config = load_config()
    headers = get_headers(config)
    
    # 验证是否提供了 Cookie
    if not config["webcatalog"]["cookie"] or "ASPXAUTH" not in config["webcatalog"]["cookie"]:
        print("Warning: WebCatalog cookie does not seem to contain '.ASPXAUTH'. Requests might fail.")
    
    total_synced = 0
    all_table_ids = set()
    
    # 1. 搜集所有需要同步的 Table ID
    for day in day_list:
        for hall in hall_list:
            table_ids = fetch_hall_map(day, hall, headers)
            all_table_ids.update(table_ids)
            
    print(f"Found total {len(all_table_ids)} unique circles to sync detail.")
    
    # 2. 载入数据库中已同步过的 ID
    if not force:
        existing_ids = get_existing_circle_ids(db_path=db_path) if db_path else get_existing_circle_ids()
        print(f"Skipping {len(existing_ids)} circles already synced in DB.")
    else:
        existing_ids = set()
        print("Force update enabled. Not skipping any circles.")

    
    skipped_count = 0
    # 3. 依次拉取详情并保存到 DB
    for i, table_id in enumerate(all_table_ids, 1):
        if table_id in existing_ids:
            skipped_count += 1
            continue
            
        print(f"[{i}/{len(all_table_ids)}] Fetching detail for Table {table_id}...")
        detail = fetch_circle_detail(table_id, headers)
        if detail:
            if db_path:
                save_circle(detail, db_path=db_path)
            else:
                save_circle(detail)
            total_synced += 1
        
        # 每次抓取后延迟 0.5 秒，避免触发服务器速率限制/被封 IP
        time.sleep(0.5)
            
    print(f"Sync complete. Successfully synced {total_synced} circles (Skipped {skipped_count} already synced).")
