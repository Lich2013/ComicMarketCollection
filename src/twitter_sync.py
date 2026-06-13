import os
import re
import json
import time
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlunparse
from playwright.sync_api import sync_playwright
from src.db import get_all_circles, save_catalog
from src.config import load_config
from openai import OpenAI


def parse_cookie_string(cookie_str: str, domain: str = ".x.com") -> list[dict]:
    """将普通的 Cookie 字符串（例如 'name1=val1; name2=val2'）解析为 Playwright 要求的 cookie 列表格式"""
    cookies = []
    if not cookie_str:
        return cookies
    parts = cookie_str.split(";")
    for part in parts:
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name:
            cookies.append({
                "name": name,
                "value": value,
                "domain": domain,
                "path": "/"
            })
    return cookies

CATALOG_KEYWORDS = ["品书", "品書", "お品書き", "新刊", "既刊", "颁布", "頒布", "委託", "委托", "セット", "おしながき", "カタログ"]

def download_image(url: str, output_dir: str) -> str:
    """下载图片并保存，返回本地相对路径"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 优化 Twitter 图片 URL 为原图/大图
    parsed = urlparse(url)
    if "pbs.twimg.com" in parsed.netloc:
        query = parse_qs(parsed.query)
        fmt = query.get("format", ["jpg"])[0]
        new_query = f"format={fmt}&name=orig"
        parsed = parsed._replace(query=new_query)
        url = urlunparse(parsed)
    else:
        fmt = "jpg"
        
    filename = os.path.basename(parsed.path)
    if "." not in filename:
        filename = f"{filename}.{fmt}"
        
    local_path = os.path.join(output_dir, filename)
    
    if os.path.exists(local_path):
        return local_path
        
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(response.content)
            return local_path
        else:
            if "name=orig" in url:
                url = url.replace("name=orig", "name=large")
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                    return local_path
            print(f"Failed to download image {url}, HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        
    return None

def extract_tweet_id(href: str) -> str:
    """从推文 URL 路径中提取 ID"""
    if not href:
        return None
    match = re.search(r"/status/(\d+)", href)
    return match.group(1) if match else None

def is_potential_catalog(text: str, circle: dict = None) -> bool:
    """判断推文文本是否包含品书或当前社团/CM 展位相关关键字"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # 1. 基础品书关键字
    if any(kw.lower() in text_lower for kw in CATALOG_KEYWORDS):
        return True
        
    # 2. 通用 CM 展会与日期相关词
    general_cm_keywords = [
        "c108", "c107", "c106", "comic market", "comicmarket", 
        "コミケット", "コミックマーケット", "コミケ", "コミ",
        "8.15", "8/15", "8.16", "8/16", "8月15", "8月16", "8.17", "8/17", "8月17",
        "土曜日", "日曜日", "土曜", "日曜"
    ]
    if any(kw.lower() in text_lower for kw in general_cm_keywords):
        return True
        
    # 3. 社团专属动态词 (名称、作者、展位)
    if circle:
        name = circle.get("name")
        author = circle.get("author")
        hall = circle.get("hall") or ""
        block = circle.get("block") or ""
        space = circle.get("space") or ""
        
        # 3.1 匹配社团名或作者名
        if name and name.lower() in text_lower:
            return True
        if author and author.lower() in text_lower:
            return True
            
        # 3.2 匹配特定展位号
        # 例如: "A45a", "A-45a", "A 45a"
        if block and space:
            space_clean = space.lower()
            block_clean = block.lower()
            
            booth_patterns = [
                f"{block_clean}{space_clean}",
                f"{block_clean}-{space_clean}",
                f"{block_clean} {space_clean}",
            ]
            
            # 支持繁简体东/東
            halls_to_check = []
            if "东" in hall or "東" in hall:
                halls_to_check = ["东", "東"]
            elif "西" in hall:
                halls_to_check = ["西"]
            elif "南" in hall:
                halls_to_check = ["南"]
                
            for bp in booth_patterns:
                if bp in text_lower:
                    return True
                for h in halls_to_check:
                    if f"{h}{bp}" in text_lower:
                        return True
                    if f"{h}地区{bp}" in text_lower:
                        return True
                        
    return False

def scrape_twitter_profile(username: str, cookies: list[dict] = None, max_tweets: int = 15, circle: dict = None, since_date: str = None) -> list[dict]:
    """使用 Playwright 抓取作者推文，优先通过 API 拦截，备用 DOM 解析，并进行严格多维度过滤"""
    tweets_data = []
    
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            if cookies:
                try:
                    context.add_cookies(cookies)
                    print(f"Injected {len(cookies)} cookies into X.com session context.")
                except Exception as e:
                    print(f"Error loading/injecting cookies: {e}")
            else:
                print("Warning: No X.com cookies provided. Might get redirected to login page.")
                
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 1. 注册 API 拦截监听器
            api_payloads = []
            def handle_response(response):
                if "UserTweets" in response.url or "UserTweetsAndReplies" in response.url:
                    try:
                        payload = response.json()
                        api_payloads.append(payload)
                    except Exception:
                        pass
                        
            page.on("response", handle_response)
            
            profile_url = f"https://x.com/{username}"
            print(f"Navigating to {profile_url}...")
            
            page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            
            # 2. 检测并点击敏感内容确认按钮（如有）
            btn = None
            for warning_text in ["View profile", "プロフィールを表示する"]:
                loc = page.locator(f'span:has-text("{warning_text}")').first
                if loc.is_visible():
                    btn = loc
                    break
            if btn:
                print("Found sensitive content warning button. Clicking to view profile...")
                btn.click(force=True)
                page.wait_for_timeout(5000)
                
            # 4. 解析时间阈值
            if not since_date:
                try:
                    config = load_config()
                    since_date = config["twitter"].get("since_date") or "2026-06-01"
                except Exception:
                    since_date = "2026-06-01"
            try:
                date_threshold = datetime.fromisoformat(f"{since_date}T00:00:00+00:00")
            except Exception:
                date_threshold = datetime.fromisoformat("2026-06-01T00:00:00+00:00")

            # 3. 滚动页面以加载更多推文并触发 API 响应 (对于高频推文用户，滚动较深以能追溯到 threshold)
            for i in range(10):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2500)
                
                # 滚动中段的提速检查：如果在前几次滚动中已成功拉取到早于时间阈值的普通推文，则说明已经追溯到位，可提前终止滚动
                if i >= 1:
                    oldest_tweet_date = None
                    if api_payloads:
                        for payload in api_payloads:
                            try:
                                result = payload.get("data", {}).get("user", {}).get("result", {})
                                timeline = result.get("timeline", {}).get("timeline", {})
                                instructions = timeline.get("instructions", [])
                                for inst in instructions:
                                    inst_type = inst.get("type")
                                    entries = []
                                    if inst_type == "TimelineAddEntries":
                                        entries = inst.get("entries", [])
                                    else:
                                        continue
                                        
                                    for entry in entries:
                                        entry_id = entry.get("entryId", "")
                                        # 排除置顶推文，仅通过普通时间流推文的创建日期进行判定
                                        if not entry_id.startswith("tweet-"):
                                            continue
                                        content = entry.get("content", {})
                                        if content.get("entryType") != "TimelineTimelineItem":
                                            continue
                                        item_content = content.get("itemContent", {})
                                        if item_content.get("itemType") != "TimelineTweet":
                                            continue
                                        tweet_results = item_content.get("tweet_results", {})
                                        res = tweet_results.get("result")
                                        if not res:
                                            continue
                                        typename = res.get("__typename")
                                        tweet_obj = None
                                        if typename == "Tweet":
                                            tweet_obj = res
                                        elif typename == "TweetWithVisibilityResults":
                                            tweet_obj = res.get("tweet")
                                        if not tweet_obj:
                                            continue
                                        
                                        legacy = tweet_obj.get("legacy", {})
                                        created_at = legacy.get("created_at", "")
                                        if created_at:
                                            try:
                                                tweet_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                                                if oldest_tweet_date is None or tweet_date < oldest_tweet_date:
                                                    oldest_tweet_date = tweet_date
                                            except Exception:
                                                pass
                            except Exception:
                                continue
                    
                    # 检查 DOM 元素作为备份
                    if oldest_tweet_date is None:
                        try:
                            tweet_elements = page.query_selector_all("article[data-testid='tweet']")
                            for elem in tweet_elements:
                                social_context = elem.query_selector("div[data-testid='socialContext']")
                                if social_context and ("置顶" in social_context.inner_text() or "Pinned" in social_context.inner_text()):
                                    continue
                                time_elem = elem.query_selector("time")
                                if time_elem:
                                    datetime_str = time_elem.get_attribute("datetime")
                                    if datetime_str:
                                        dt_str = datetime_str.replace("Z", "+00:00")
                                        tweet_date = datetime.fromisoformat(dt_str)
                                        if oldest_tweet_date is None or tweet_date < oldest_tweet_date:
                                            oldest_tweet_date = tweet_date
                        except Exception:
                            pass
                    
                    if oldest_tweet_date and oldest_tweet_date < date_threshold:
                        print(f"Oldest tweet found ({oldest_tweet_date}) is older than threshold ({date_threshold}). Breaking scroll loop early at scroll {i+1}.")
                        break
            
            if api_payloads:
                print(f"Parsing {len(api_payloads)} intercepted GraphQL API responses...")
                parsed_tweets = {}
                for payload in api_payloads:
                    if len(parsed_tweets) >= 500:
                        break
                    try:
                        result = payload.get("data", {}).get("user", {}).get("result", {})
                        timeline = result.get("timeline", {}).get("timeline", {})
                        instructions = timeline.get("instructions", [])
                    except Exception:
                        continue
                        
                    for inst in instructions:
                        if len(parsed_tweets) >= 500:
                            break
                        inst_type = inst.get("type")
                        entries = []
                        if inst_type == "TimelineAddEntries":
                            entries = inst.get("entries", [])
                        elif inst_type == "TimelinePinEntry":
                            pin_entry = inst.get("entry")
                            if pin_entry:
                                entries = [pin_entry]
                        else:
                            continue
                            
                        for entry in entries:
                            if len(parsed_tweets) >= 500:
                                break
                            entry_id = entry.get("entryId", "")
                            if not (entry_id.startswith("tweet-") or entry_id.startswith("pinnedEntry-")):
                                continue
                            content = entry.get("content", {})
                            if content.get("entryType") != "TimelineTimelineItem":
                                continue
                            item_content = content.get("itemContent", {})
                            if item_content.get("itemType") != "TimelineTweet":
                                continue
                            tweet_results = item_content.get("tweet_results", {})
                            res = tweet_results.get("result")
                            if not res:
                                continue
                                
                            typename = res.get("__typename")
                            tweet_obj = None
                            if typename == "Tweet":
                                tweet_obj = res
                            elif typename == "TweetWithVisibilityResults":
                                tweet_obj = res.get("tweet")
                                
                            if not tweet_obj:
                                continue
                                
                            legacy = tweet_obj.get("legacy", {})
                            tweet_id = tweet_obj.get("rest_id")
                            
                            # 用外部推文的发布时间做阈值判定
                            created_at = legacy.get("created_at", "")
                            
                            # 时间过滤
                            if created_at:
                                try:
                                    tweet_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                                except Exception:
                                    tweet_date = None
                                    
                                if tweet_date:
                                    # Pinned tweet (either entry starts with pinnedEntry or it came from TimelinePinEntry)
                                    is_pinned = entry_id.startswith("pinnedEntry-") or inst_type == "TimelinePinEntry"
                                    if not is_pinned and tweet_date < date_threshold:
                                        continue
                                    if is_pinned and tweet_date < date_threshold:
                                        # 即使是置顶推文，也可以在这里进行过滤或者保留
                                        continue
                                        
                            # 原创/自转校验 (检查外部推文的正文)
                            outer_text = legacy.get("full_text", "")
                            rt_match = re.match(r"^RT @(\w+):", outer_text)
                            if rt_match:
                                if rt_match.group(1).lower() != username.lower():
                                    continue
                                    
                            # 若为转发/自转，提取原始推文的 legacy 对象以读取图片和完整文本，并归一化为原推 ID
                            retweet_legacy = legacy
                            original_tweet_id = tweet_id
                            retweet_res = legacy.get("retweeted_status_result", {}).get("result")
                            if retweet_res:
                                rt_typename = retweet_res.get("__typename")
                                rt_obj = None
                                if rt_typename == "Tweet":
                                    rt_obj = retweet_res
                                elif rt_typename == "TweetWithVisibilityResults":
                                    rt_obj = retweet_res.get("tweet")
                                if rt_obj:
                                    retweet_legacy = rt_obj.get("legacy", legacy)
                                    original_tweet_id = rt_obj.get("rest_id", tweet_id)
                                    
                            resolved_text = retweet_legacy.get("full_text", "")
                            
                            # 提取图片资源 (从解析后的 legacy 中)
                            img_urls = []
                            ext_entities = retweet_legacy.get("extended_entities", {})
                            for media in ext_entities.get("media", []):
                                if media.get("type") == "photo":
                                    img_urls.append(media.get("media_url_https"))
                            if not img_urls:
                                continue
                                
                            # 上下文关键字匹配
                            if is_potential_catalog(resolved_text, circle):
                                parsed_tweets[original_tweet_id] = {
                                    "tweet_id": original_tweet_id,
                                    "tweet_url": f"https://x.com/{username}/status/{original_tweet_id}",
                                    "tweet_text": resolved_text,
                                    "image_urls": img_urls
                                }
                if parsed_tweets:
                    tweets_data = list(parsed_tweets.values())
                    print(f"Extracted {len(tweets_data)} matching tweets from API interception.")
                    
            # 5. 如果 API 没截获到或者没解析出内容，降级为 DOM 渲染提取
            if not tweets_data:
                print("Falling back to DOM parsing...")
                tweet_elements = page.query_selector_all("article[data-testid='tweet']")
                print(f"Found {len(tweet_elements)} tweet elements on page via DOM.")
                
                for elem in tweet_elements[:max_tweets]:
                    try:
                        # 提取发布时间
                        time_elem = elem.query_selector("time")
                        if not time_elem:
                            continue
                        datetime_str = time_elem.get_attribute("datetime")
                        if not datetime_str:
                            continue
                        dt_str = datetime_str.replace("Z", "+00:00")
                        tweet_date = datetime.fromisoformat(dt_str)
                        
                        # 判断是否为置顶
                        is_pinned = False
                        social_context = elem.query_selector("div[data-testid='socialContext']")
                        if social_context and ("置顶" in social_context.inner_text() or "Pinned" in social_context.inner_text()):
                            is_pinned = True
                        
                        if not is_pinned and tweet_date < date_threshold:
                            break
                        if is_pinned and tweet_date < date_threshold:
                            continue
                            
                        # 提取链接
                        link_elem = elem.query_selector("a[href*='/status/']")
                        if not link_elem:
                            continue
                        href = link_elem.get_attribute("href")
                        parts = href.strip("/").split("/")
                        if parts and parts[0].lower() != username.lower():
                            continue
                        tweet_id = extract_tweet_id(href)
                        if not tweet_id:
                            continue
                        tweet_url = f"https://x.com{href}"
                        
                        # 提取图片
                        img_urls = []
                        img_elems = elem.query_selector_all("img[src*='pbs.twimg.com/media/']")
                        for img in img_elems:
                            src = img.get_attribute("src")
                            if src and src not in img_urls:
                                img_urls.append(src)
                        if not img_urls:
                            continue
                            
                        # 文本
                        text_elem = elem.query_selector("div[data-testid='tweetText']")
                        tweet_text = text_elem.inner_text() if text_elem else ""
                        
                        if is_potential_catalog(tweet_text, circle):
                            tweets_data.append({
                                "tweet_id": tweet_id,
                                "tweet_url": tweet_url,
                                "tweet_text": tweet_text,
                                "image_urls": img_urls
                            })
                    except Exception as inner_e:
                        print(f"Error parsing DOM element: {inner_e}")
                        
        except Exception as e:
            print(f"Error scraping profile {username}: {e}")
            if 'page' in locals() and page:
                try:
                    screenshot_path = f"data/error_{username}.png"
                    os.makedirs("data", exist_ok=True)
                    page.screenshot(path=screenshot_path)
                    print(f"Saved error screenshot to {screenshot_path}")
                except Exception:
                    pass
        finally:
            if browser:
                browser.close()
            
    return tweets_data

def sync_circle_twitter(circle: dict, cookies: list[dict] = None, db_path: str = None) -> int:
    """同步单个社团的 Twitter 推文及品书图片"""
    username = circle.get("twitter_username")
    circle_id = circle.get("id")
    
    if not username:
        return 0
        
    print(f"--- Starting Twitter sync for Circle '{circle.get('name')}' (@{username}) ---")
    config = load_config()
    since_date = config["twitter"].get("since_date")
    tweets = scrape_twitter_profile(username, cookies=cookies, circle=circle, since_date=since_date)
    print(f"Found {len(tweets)} potential catalog tweets for @{username}.")
    
    # Apply LLM text pre-filtering if enabled
    config = load_config()
    analysis_config = config.get("tweet_analysis", {})
    if analysis_config.get("enabled", False):
        print(f"Applying LLM text pre-filtering for @{username}...")
        filtered_tweets = []
        for tweet in tweets:
            if analyze_tweet_text_with_llm(tweet["tweet_text"], circle, analysis_config):
                filtered_tweets.append(tweet)
        tweets = filtered_tweets
        print(f"After LLM pre-filtering, found {len(tweets)} matching catalog tweets.")
        
    synced_count = 0
    image_dir = f"data/images/{circle_id}"
    
    for tweet in tweets:
        tweet_id = tweet["tweet_id"]
        for idx, img_url in enumerate(tweet["image_urls"]):
            local_path = download_image(img_url, image_dir)
            if local_path:
                catalog_data = {
                    "circle_id": circle_id,
                    "tweet_id": f"{tweet_id}_{idx}",
                    "tweet_url": tweet["tweet_url"],
                    "tweet_text": tweet["tweet_text"],
                    "image_path": local_path,
                    "status": "pending"
                }
                if db_path:
                    save_catalog(catalog_data, db_path=db_path)
                else:
                    save_catalog(catalog_data)
                synced_count += 1
                
    return synced_count

def sync_all_circles_twitter(
    db_path: str = None,
    day_list: list[str] = None,
    hall_list: list[str] = None,
    circle_ids: list[int] = None,
    name_query: str = None
):
    """同步数据库中指定或所有社团的 Twitter 推文"""
    config = load_config()
    
    # 解析 Twitter Cookies
    cookies = []
    # 1. 优先使用 cookie_string 配置 (支持普通 name=value; 字符串)
    cookie_string = config["twitter"].get("cookie_string")
    if cookie_string:
        cookies = parse_cookie_string(cookie_string)
        print("Using X.com cookie_string from config.")
    # 2. 其次尝试从 cookies_file 读取
    else:
        cookies_file = config["twitter"].get("cookies_file")
        if cookies_file and os.path.exists(cookies_file):
            try:
                with open(cookies_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    # 自动检测是 JSON 还是普通的 Cookie 文本
                    if content.startswith("[") and content.endswith("]"):
                        cookies = json.loads(content)
                        print(f"Loaded X.com cookies (JSON format) from {cookies_file}.")
                    else:
                        cookies = parse_cookie_string(content)
                        print(f"Loaded and parsed X.com cookies (String format) from {cookies_file}.")
            except Exception as e:
                print(f"Error loading cookies from {cookies_file}: {e}")
        else:
            print("Warning: X.com cookies_file / cookie_string not configured or not found.")

    # 确定要同步的社团 ID 集合
    # 如果指定了任何筛选条件，调用 get_filtered_circle_ids 获得符合条件的 ID 集合
    has_filter = any(x is not None for x in [day_list, hall_list, circle_ids, name_query])
    
    if has_filter:
        db_to_use = db_path if db_path else "data/comic_market.db"
        from src.db import get_filtered_circle_ids
        target_ids = get_filtered_circle_ids(day_list, hall_list, circle_ids, name_query, db_path=db_to_use)
        print(f"Applying filters. Found {len(target_ids)} matching circle(s) to sync.")
        if not target_ids:
            print("No matching circles found. Skipping Twitter sync.")
            return
    else:
        target_ids = None

    circles = get_all_circles(db_path=db_path) if db_path else get_all_circles()
    
    # 根据 ID 过滤
    if target_ids is not None:
        circles = [c for c in circles if c.get("id") in target_ids]
        
    active_circles = [c for c in circles if c.get("twitter_username")]
    
    print(f"Found {len(active_circles)} circles with Twitter username configured.")
    
    total_catalogs = 0
    for circle in active_circles:
        try:
            count = sync_circle_twitter(circle, cookies=cookies, db_path=db_path)
            total_catalogs += count
            time.sleep(3)
        except Exception as e:
            print(f"Failed to sync Twitter for circle {circle.get('name')}: {e}")
            
    print(f"All Twitter sync completed. Synced {total_catalogs} catalog images.")

def scrape_single_tweet(tweet_url: str, cookies: list[dict] = None) -> dict:
    """使用 Playwright 抓取单条 X 博文详情，通过 API 拦截，备用 DOM 解析"""
    parsed_tweet = None
    
    # 提取 username 和 tweet_id
    match = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d+)", tweet_url)
    if not match:
        print(f"Error: Invalid X.com tweet URL: {tweet_url}")
        return None
        
    username, tweet_id = match.group(1), match.group(2)
    
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            if cookies:
                try:
                    context.add_cookies(cookies)
                    print(f"Injected {len(cookies)} cookies into X.com session context.")
                except Exception as e:
                    print(f"Error loading/injecting cookies: {e}")
                    
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 1. 注册 API 拦截监听器
            api_payloads = []
            def handle_response(response):
                if "TweetDetail" in response.url:
                    try:
                        payload = response.json()
                        api_payloads.append(payload)
                    except Exception:
                        pass
                        
            page.on("response", handle_response)
            
            print(f"Navigating to tweet detail page: {tweet_url}...")
            page.goto(tweet_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            
            # 2. 检测并点击敏感内容确认按钮（如有）
            btn = None
            for warning_text in ["View profile", "プロフィールを表示する", "表示する", "View"]:
                loc = page.locator(f'span:has-text("{warning_text}")').first
                if loc.is_visible():
                    btn = loc
                    break
            if btn:
                print("Found sensitive warning button. Clicking to view content...")
                btn.click(force=True)
                page.wait_for_timeout(3000)
                
            # 3. 解析被拦截的 API 响应
            if api_payloads:
                print(f"Parsing {len(api_payloads)} intercepted TweetDetail GraphQL API responses...")
                for payload in api_payloads:
                    try:
                        instructions = (
                            payload.get("data", {})
                            .get("threaded_conversation_with_injections_v2", {})
                            .get("instructions", [])
                        )
                    except Exception:
                        continue
                        
                    for inst in instructions:
                        if inst.get("type") != "TimelineAddEntries":
                            continue
                        for entry in inst.get("entries", []):
                            entry_id = entry.get("entryId", "")
                            # 必须匹配 target tweet_id
                            if entry_id != f"tweet-{tweet_id}":
                                continue
                                
                            content = entry.get("content", {})
                            if content.get("entryType") != "TimelineTimelineItem":
                                continue
                            item_content = content.get("itemContent", {})
                            if item_content.get("itemType") != "TimelineTweet":
                                continue
                            tweet_results = item_content.get("tweet_results", {})
                            res = tweet_results.get("result")
                            if not res:
                                continue
                                
                            typename = res.get("__typename")
                            tweet_obj = None
                            if typename == "Tweet":
                                tweet_obj = res
                            elif typename == "TweetWithVisibilityResults":
                                tweet_obj = res.get("tweet")
                                
                            if not tweet_obj:
                                continue
                                
                            legacy = tweet_obj.get("legacy", {})
                            
                            # 若为转发/自转，提取原始推文的 legacy 对象以读取图片和完整文本，并归一化为原推 ID
                            retweet_legacy = legacy
                            original_tweet_id = tweet_id
                            retweet_res = legacy.get("retweeted_status_result", {}).get("result")
                            if retweet_res:
                                rt_typename = retweet_res.get("__typename")
                                rt_obj = None
                                if rt_typename == "Tweet":
                                    rt_obj = retweet_res
                                elif rt_typename == "TweetWithVisibilityResults":
                                    rt_obj = retweet_res.get("tweet")
                                if rt_obj:
                                    retweet_legacy = rt_obj.get("legacy", legacy)
                                    original_tweet_id = rt_obj.get("rest_id", tweet_id)
                                    
                            resolved_text = retweet_legacy.get("full_text", "")
                            
                            img_urls = []
                            ext_entities = retweet_legacy.get("extended_entities", {})
                            for media in ext_entities.get("media", []):
                                if media.get("type") == "photo":
                                    img_urls.append(media.get("media_url_https"))
                                    
                            parsed_tweet = {
                                "tweet_id": original_tweet_id,
                                "tweet_url": f"https://x.com/{username}/status/{original_tweet_id}",
                                "tweet_text": resolved_text,
                                "image_urls": img_urls
                            }
                            break
                        if parsed_tweet:
                            break
                    if parsed_tweet:
                        break
                        
            # 4. DOM 备份解析（如果 API 没截获到）
            if not parsed_tweet:
                print("Falling back to DOM parsing for single tweet...")
                tweet_elem = page.query_selector("article[data-testid='tweet']")
                if tweet_elem:
                    try:
                        # 提取图片
                        img_urls = []
                        img_elems = tweet_elem.query_selector_all("img[src*='pbs.twimg.com/media/']")
                        for img in img_elems:
                            src = img.get_attribute("src")
                            if src and src not in img_urls:
                                img_urls.append(src)
                                
                        # 提取文本
                        text_elem = tweet_elem.query_selector("div[data-testid='tweetText']")
                        tweet_text = text_elem.inner_text() if text_elem else ""
                        
                        parsed_tweet = {
                            "tweet_id": tweet_id,
                            "tweet_url": tweet_url,
                            "tweet_text": tweet_text,
                            "image_urls": img_urls
                        }
                    except Exception as dom_e:
                        print(f"Error parsing single tweet DOM: {dom_e}")
                        
        except Exception as e:
            print(f"Error scraping single tweet {tweet_url}: {e}")
            if 'page' in locals() and page:
                try:
                    screenshot_path = f"data/error_tweet_{tweet_id}.png"
                    os.makedirs("data", exist_ok=True)
                    page.screenshot(path=screenshot_path)
                    print(f"Saved error screenshot to {screenshot_path}")
                except Exception:
                    pass
        finally:
            if browser:
                browser.close()
            
    return parsed_tweet

def sync_single_tweet(tweet_url: str, circle_id: int = None, cookies_file: str = None, db_path: str = None) -> bool:
    """手动同步指定的一条 X 博文链接并保存品书图片"""
    config = load_config()
    
    # 提取 username 
    match = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d+)", tweet_url)
    if not match:
        print(f"Error: Invalid X.com tweet URL format: {tweet_url}")
        return False
    username, tweet_id = match.group(1), match.group(2)
    
    # 查找关联社团
    db_to_use = db_path if db_path else "data/comic_market.db"
    if not circle_id:
        import sqlite3
        conn = sqlite3.connect(db_to_use)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM circles WHERE LOWER(twitter_username) = ?", (username.lower(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            circle_id = row["id"]
            print(f"Found matching circle '{row['name']}' (ID: {circle_id}) for username '@{username}'.")
        else:
            print(f"Error: No circle found in database with twitter_username '@{username}'.")
            print("Please run WebCatalog sync first, or specify a circle ID manually using --circle-ids.")
            return False
            
    # 解析 Cookies
    cookies = []
    cookie_string = config["twitter"].get("cookie_string")
    if cookie_string:
        cookies = parse_cookie_string(cookie_string)
        print("Using X.com cookie_string from config.")
    else:
        actual_cookies_file = cookies_file or config["twitter"].get("cookies_file")
        if actual_cookies_file and os.path.exists(actual_cookies_file):
            try:
                with open(actual_cookies_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    if content.startswith("[") and content.endswith("]"):
                        cookies = json.loads(content)
                        print(f"Loaded X.com cookies (JSON format) from {actual_cookies_file}.")
                    else:
                        cookies = parse_cookie_string(content)
                        print(f"Loaded and parsed X.com cookies (String format) from {actual_cookies_file}.")
            except Exception as e:
                print(f"Error loading cookies from {actual_cookies_file}: {e}")
                
    # 抓取博文
    tweet = scrape_single_tweet(tweet_url, cookies=cookies)
    if not tweet:
        print("Failed to scrape single tweet content.")
        return False
        
    # 保存图片与落库
    image_dir = f"data/images/{circle_id}"
    synced_count = 0
    
    if not tweet["image_urls"]:
        print("Warning: The target tweet does not contain any images.")
        
    for idx, img_url in enumerate(tweet["image_urls"]):
        local_path = download_image(img_url, image_dir)
        if local_path:
            catalog_data = {
                "circle_id": circle_id,
                "tweet_id": f"{tweet_id}_{idx}",
                "tweet_url": tweet["tweet_url"],
                "tweet_text": tweet["tweet_text"],
                "image_path": local_path,
                "status": "pending"
            }
            save_catalog(catalog_data, db_path=db_to_use)
            synced_count += 1
            
    print(f"Successfully synced single tweet. Saved {synced_count} catalog images for Circle ID {circle_id}.")
    return synced_count > 0

def analyze_tweet_text_with_llm(text: str, circle: dict, analysis_config: dict) -> bool:
    """使用指定的 OpenAI 兼容大语言模型预分析推文文本，判断其是否为品书/新刊宣发推文"""
    api_key = analysis_config.get("api_key")
    base_url = analysis_config.get("base_url", "https://api.openai.com/v1")
    model = analysis_config.get("model", "gpt-4o-mini")
    
    if not api_key:
        print("Warning: tweet_analysis api_key is not configured. Skipping LLM pre-filtering.")
        return True
        
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    system_prompt = (
        "You are an expert assistant for Comic Market (Comiket) event participants. "
        "Your task is to analyze the text of a tweet and determine if the author is announcing or "
        "sharing their catalog, menu, new book details, or booth information (お品書き, 品书, 新刊, 颁布, 摊位等) for the event.\n"
        "Respond ONLY with a JSON object containing:\n"
        "{\n"
        "  \"is_catalog_announcement\": true/false,\n"
        "  \"reason\": \"A brief explanation in English or Chinese\"\n"
        "}"
    )
    
    user_prompt = f"Analyze the following tweet text:\n---\n{text}\n---"
    if circle:
        user_prompt += f"\nCircle Info:\nName: {circle.get('name')}\nAuthor: {circle.get('author')}\nBooth: {circle.get('hall', '')} {circle.get('block', '')} {circle.get('space', '')}"
        
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},  # Standard JSON mode
            timeout=15
        )
        content = response.choices[0].message.content.strip()
        
        # 兼容 Markdown 格式包裹
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        res_json = json.loads(content)
        is_catalog = res_json.get("is_catalog_announcement", False)
        reason = res_json.get("reason", "")
        print(f"LLM tweet pre-filtering analysis result for text [{text[:30]}...]: {is_catalog} (Reason: {reason})")
        return is_catalog
    except Exception as e:
        print(f"Error during LLM text analysis: {e}. Defaulting to True to avoid missing data.")
        return True

