import io
import json
import base64
import os
import re
import shlex
import subprocess
from PIL import Image
from pydantic import BaseModel, Field
from src.utils.observability import get_openai_client

from src.db import get_pending_catalogs, save_goods, update_catalog_status
from src.config import load_config

# --- 默认 Prompt 模版 ---
DEFAULT_PROMPT_TEMPLATE = (
    "【注意：请仅扮演图片视觉识别助手。你唯一被允许的事情是使用视觉查看工具读取指定的图片路径，禁止检索、阅读或分析本地代码仓（如 src 目录）中的任何文件，禁止调用测试或查询数据库。】\n"
    "请使用你的视觉工具查看并分析以下路径的图片文件：{image_path}。\n"
    "这张图片是 Comic Market 社团“{circle_name}”（作者：“{circle_author}”）的展位宣传图或品书。\n\n"
    "请执行以下提取任务：\n"
    "1. 判断该图片是否是品书/お品書き（即包含同人本、制品、周边清单及其日元价格的版面）。如果属于品书且有商品列表，设置 `is_catalog` 为 true；否则为 false。\n"
    "2. 如果 `is_catalog` 为 true，提取其中列出的所有商品信息。对于每项商品，提取名称 (name)、类型 (type)、价格 (price: 整数) 以及是否为套装 (is_set)。\n\n"
    "提取商品名称 (name) 时，符号（波浪线、括号、空格等）必须统一使用半角字符。例如：使用 '~' 而非 '～' 或 '〜'，使用 '(' ')' 而非 '（' '）'，数字和英文字母也使用半角。日文和中文文字保持原样。\n\n"
    "请严格以下面的 JSON 格式输出结果，不要包含任何多余的前后解释和文字：\n"
    "{\n"
    "  \"is_catalog\": true/false,\n"
    "  \"items\": [\n"
    "    {\n"
    "      \"name\": \"商品名称\",\n"
    "      \"type\": \"新刊/既刊/周边/套装\",\n"
    "      \"price\": 1000,\n"
    "      \"is_set\": true/false\n"
    "    }\n"
    "  ]\n"
    "}"
)

# --- Pydantic 结构定义 ---

class GoodsItem(BaseModel):
    name: str = Field(description="同人制品或书籍的名称。保留原始语言（通常为日语，如：『新刊』C107合同誌）。")
    type: str = Field(description="制品类型。例如：'新刊', '既刊', '周边' (包含挂件、立牌等周边), '套装' (Set)。")
    price: int = Field(description="价格（日元）。提取为整数。如果未标明或免费，则设为 0。")
    is_set: bool = Field(description="如果该项代表一个套装/Set（包含多个制品），则为 True。")

class CatalogExtraction(BaseModel):
    is_catalog: bool = Field(description="如果图片确实是 Comic Market 的品书/お品書き（包含制品及价格列表），则为 True；否则为 False。")
    items: list[GoodsItem] = Field(description="从品书中提取出的同人制品列表。")

# --- 辅助函数 ---

def encode_image_to_jpeg_base64(image_path: str, max_size: int = 1500) -> str:
    """加载图片，按比例缩放，并转换为 JPEG 的 base64 编码"""
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        width, height = img.size
        if max(width, height) > max_size:
            ratio = max_size / max(width, height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 强容错数据清洗与解析器 ---

def clean_price(price_raw) -> int:
    """清洗价格字段，支持 '1,000円', '￥500', 1000.0 等各种脏数据"""
    if isinstance(price_raw, (int, float)):
        return int(price_raw)
    if not price_raw:
        return 0
        
    price_str = str(price_raw).strip()
    price_str = re.sub(r"[^\d]", "", price_str)
    try:
        return int(price_str) if price_str else 0
    except ValueError:
        return 0

def clean_boolean(val) -> bool:
    """清洗布尔字段，支持 'yes', 'no', '1', 0 等各种布尔表达方式"""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes", "y", "套装", "set")
    return False

def fuzzy_normalize_item(raw_item: dict) -> dict:
    """模糊键名匹配器：将各类异形 key 映射归一化为 name, type, price, is_set"""
    name_candidates = ["name", "title", "product", "book", "goods", "item", "名称", "新刊"]
    type_candidates = ["type", "category", "genre", "类型"]
    price_candidates = ["price", "cost", "yen", "amount", "value", "价格", "金额"]
    set_candidates = ["is_set", "set", "has_set", "is_package", "套装"]
    
    normalized = {"name": "", "type": "其他", "price": 0, "is_set": False}
    
    for k in name_candidates:
        if k in raw_item:
            normalized["name"] = str(raw_item[k]).strip()
            break
            
    for k in type_candidates:
        if k in raw_item:
            normalized["type"] = str(raw_item[k]).strip()
            break
            
    for k in price_candidates:
        if k in raw_item:
            normalized["price"] = clean_price(raw_item[k])
            break
            
    for k in set_candidates:
        if k in raw_item:
            normalized["is_set"] = clean_boolean(raw_item[k])
            break
    else:
        name_lower = normalized["name"].lower()
        if any(x in name_lower for x in ["set", "套装", "セット", "合同誌セット"]):
            normalized["is_set"] = True
            
    return normalized

def parse_json_from_stdout(stdout_text: str) -> tuple[bool, bool, list]:
    """稳健地截取并解析 CLI 标准输出中的 JSON 块"""
    stdout_text = stdout_text.strip()
    
    # 1. 首先尝试直接解析整个 stdout
    try:
        data = json.loads(stdout_text)
        if isinstance(data, dict):
            is_catalog = clean_boolean(data.get("is_catalog", True))
            items = data.get("items", [])
            return True, is_catalog, items
        elif isinstance(data, list):
            return True, True, data
    except Exception:
        pass

    # 2. 尝试寻找 markdown json 代码块
    match = re.search(r"```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```", stdout_text, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                is_catalog = clean_boolean(data.get("is_catalog", True))
                items = data.get("items", [])
                return True, is_catalog, items
            elif isinstance(data, list):
                return True, True, data
        except Exception:
            pass

    # 3. 智能寻找大括号/中括号
    start_obj = stdout_text.find('{')
    end_obj = stdout_text.rfind('}')
    start_arr = stdout_text.find('[')
    end_arr = stdout_text.rfind(']')
    
    json_str = None
    if start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
        if end_arr > start_arr:
            json_str = stdout_text[start_arr:end_arr+1]
    elif start_obj != -1:
        if end_obj > start_obj:
            json_str = stdout_text[start_obj:end_obj+1]
            
    if json_str:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                is_catalog = clean_boolean(data.get("is_catalog", True))
                items = data.get("items", [])
                return True, is_catalog, items
            elif isinstance(data, list):
                return True, True, data
        except Exception:
            pass
            
    return False, False, []

def try_parse_markdown_list(stdout_text: str) -> list[dict]:
    """尝试用正则解析 Markdown 列表 (例如 '- 商品名 1000円' 或 '* 商品名 ￥500')"""
    items = []
    lines = stdout_text.split("\n")
    # 匹配模式：列表符 [空格] 商品名 [空格/破折号/冒号/￥等] 价格 [円/元/等]
    pattern = re.compile(r"^[-*+]\s+(.+?)\s*[-:：——￥$¥]*\s*(\d[\d,]*)\s*[円元$¥]?$")
    
    for line in lines:
        line = line.strip()
        match = pattern.match(line)
        if match:
            name_raw = match.group(1).strip()
            price_raw = match.group(2)
            
            is_set = any(x in name_raw.lower() for x in ["set", "套装", "セット", "合同誌セット"])
            items.append({
                "name": name_raw,
                "type": "套装" if is_set else "新刊",
                "price": clean_price(price_raw),
                "is_set": is_set
            })
            
    return items

def format_unstructured_text_via_api(unstructured_text: str, config: dict) -> list[dict]:
    """调用纯文本大模型将非结构化文本整理为标准的商品列表"""
    analysis_config = config.get("tweet_analysis", {})
    openai_config = config.get("openai", {})
    
    api_key = analysis_config.get("api_key") or openai_config.get("api_key")
    base_url = analysis_config.get("base_url") or openai_config.get("base_url")
    model = analysis_config.get("model") or openai_config.get("model", "gpt-4o-mini")
    
    if not api_key:
        print("Warning: API Key missing for fallback text formatting.")
        return []
        
    client = get_openai_client(api_key=api_key, base_url=base_url)
    
    system_prompt = (
        "You are an expert parsing assistant. Your task is to read the unstructured text input, "
        "identify Comic Market goods/books/sets and their JPY prices, and output a standard JSON list. "
        "Your response MUST be ONLY a JSON array of items, each having: "
        '{"name": "string", "type": "string", "price": integer, "is_set": boolean}. '
        "Do NOT write any conversational text or explanation. Only output standard JSON."
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse the following text:\n{unstructured_text}"}
            ],
            response_format={"type": "json_object"},
            timeout=20
        )
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "items" in data and isinstance(data["items"], list):
                return data["items"]
            return [data]
    except Exception as e:
        print(f"Failed to format unstructured text via API: {e}")
        
    return []

# --- 核心提取子引擎 ---

def extract_goods_via_openai(catalog: dict, openai_config: dict) -> tuple[bool, list]:
    """使用 OpenAI 多模态 API 解析单张品书图"""
    image_path = catalog.get("image_path")
    circle_name = catalog.get("circle_name", "未知社团")
    
    api_key = openai_config.get("api_key")
    base_url = openai_config.get("base_url")
    model = openai_config.get("model", "gpt-4o-mini")
    
    if not api_key:
        raise ValueError("OpenAI API key is missing. Please set OPENAI_API_KEY environment variable or configure config.yaml.")
        
    client = get_openai_client(api_key=api_key, base_url=base_url)
    
    try:
        base64_image = encode_image_to_jpeg_base64(image_path)
    except Exception as e:
        print(f"Failed to read/process image {image_path}: {e}")
        return False, []
        
    system_prompt = (
        "You are an expert assistant for Comic Market (Comiket) event participants. "
        "Your task is to review catalog infographics (品书 / お品書き) and extract all listed doujin books and goods. "
        "Make sure to extract JPY prices accurately (e.g., 1000円, ￥500, or 500 should be extracted as integer 1000 or 500)."
    )
    
    user_prompt = (
        "Analyze the provided image.\n"
        "1. Identify if this image is a catalog sheet (品书 / お品書き) listing books, goods, or sets with their prices. "
        "Set `is_catalog` accordingly.\n"
        "2. If `is_catalog` is true, extract all items. For each item, identify its name, type, price (in JPY), and whether it is a set."
    )
    
    try:
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "content": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format=CatalogExtraction,
            timeout=60
        )
        result = response.choices[0].message.parsed
        if result:
            return result.is_catalog, result.items
    except Exception as parse_error:
        print(f"Structured outputs failed, trying standard JSON Mode fallback: {parse_error}")
        try:
            json_user_prompt = (
                f"{user_prompt}\n"
                "You MUST respond ONLY with a JSON object matching this schema:\n"
                "{\n"
                "  \"is_catalog\": true/false,\n"
                "  \"items\": [\n"
                "    {\n"
                "      \"name\": \"item name\",\n"
                "      \"type\": \"item type\",\n"
                "      \"price\": 1000,\n"
                "      \"is_set\": true/false\n"
                "    }\n"
                "  ]\n"
                "}"
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "content": json_user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                timeout=60
            )
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
                
            result = CatalogExtraction.model_validate_json(content)
            if result:
                return result.is_catalog, result.items
        except Exception as fallback_error:
            print(f"JSON Mode fallback also failed: {fallback_error}")
            
    return False, []

def extract_goods_via_cmd(catalog: dict, cmd_config: dict, config: dict) -> tuple[bool, list]:
    """使用自定义命令行进行品书图像识别"""
    image_path = catalog.get("image_path", "")
    abs_image_path = os.path.abspath(image_path)
    circle_name = catalog.get("circle_name", "未知社团")
    circle_author = catalog.get("circle_author", "未知作者")
    
    command = cmd_config.get("command", "agy")
    args = cmd_config.get("args", ["-p", "{prompt}"])
    timeout = cmd_config.get("timeout", 180)
    
    # 预压缩配置解析
    compress = cmd_config.get("compress", False)
    max_size = cmd_config.get("max_size", 1500)
    quality = cmd_config.get("quality", 85)
    
    temp_image_path = None
    target_image_path = image_path
    target_abs_image_path = abs_image_path
    
    if compress and image_path and os.path.exists(image_path):
        import time
        try:
            tmp_dir = os.path.join("data", "images", "tmp")
            os.makedirs(tmp_dir, exist_ok=True)
            
            timestamp = int(time.time() * 1000)
            base_name = os.path.basename(image_path)
            name_part, _ = os.path.splitext(base_name)
            temp_filename = f"tmp_{timestamp}_{name_part}.jpg"
            temp_image_path = os.path.join(tmp_dir, temp_filename)
            
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                w, h = img.size
                if max(w, h) > max_size:
                    ratio = max_size / max(w, h)
                    new_size = (int(w * ratio), int(h * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                img.save(temp_image_path, format="JPEG", quality=quality)
                
            comp_size = os.path.getsize(temp_image_path)
            orig_size = os.path.getsize(image_path)
            if comp_size >= orig_size * 0.9:
                print(f"Compressed image size ({comp_size/1024:.1f}KB) is >= 90% of original ({orig_size/1024:.1f}KB). Falling back to original image.")
                os.remove(temp_image_path)
                temp_image_path = None
            else:
                target_image_path = temp_image_path
                target_abs_image_path = os.path.abspath(temp_image_path)
        except Exception as e:
            print(f"Warning: Failed to pre-compress image {image_path}: {e}. Falling back to original image.")
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.remove(temp_image_path)
                except Exception:
                    pass
            temp_image_path = None
            
    try:
        # 构造 Prompt
        prompt_template = cmd_config.get("prompt_template", DEFAULT_PROMPT_TEMPLATE)
        prompt = prompt_template.replace("{image_path}", target_image_path) \
                                 .replace("{abs_image_path}", target_abs_image_path) \
                                 .replace("{circle_name}", circle_name) \
                                 .replace("{circle_author}", circle_author)
        
        # 处理参数列表中的占位符
        processed_args = []
        for arg in args:
            processed_arg = arg.replace("{prompt}", prompt) \
                               .replace("{image_path}", target_image_path) \
                               .replace("{abs_image_path}", target_abs_image_path) \
                               .replace("{circle_name}", circle_name) \
                               .replace("{circle_author}", circle_author)
            processed_args.append(processed_arg)
            
        cmd_parts = shlex.split(command)
        full_cmd = cmd_parts + processed_args
        print(f"Executing custom recognition command: {' '.join(shlex.quote(x) for x in full_cmd)}")
        
        result = subprocess.run(
            full_cmd,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # 打印调试日志，方便用户定位 CLI 的返回结果
        print(f"--- CLI Execution Debug Log ---")
        print(f"Exit Code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout.strip()}")
        print(f"STDERR:\n{result.stderr.strip()}")
        print(f"--------------------------------")
        
        if result.returncode != 0:
            print(f"Command failed with code {result.returncode}. Stderr: {result.stderr}")
            return False, []
            
        stdout_content = result.stdout.strip()
        
        # 1. 尝试解析 JSON
        parsed_ok, is_catalog, raw_items = parse_json_from_stdout(stdout_content)
        if parsed_ok:
            return is_catalog, raw_items
            
        # 2. 解析失败时，尝试解析 Markdown 列表形式
        raw_items = try_parse_markdown_list(stdout_content)
        if raw_items:
            return True, raw_items
            
        # 3. 如果仍无结果，且开启了 fallback_text_formatter，调用纯文本 API 进行转换
        if cmd_config.get("fallback_text_formatter", True):
            print("CLI output parsing failed. Falling back to low-cost text-to-JSON API parser...")
            raw_items = format_unstructured_text_via_api(stdout_content, config)
            if raw_items:
                return True, raw_items
            
        return False, []
        
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds.")
    except Exception as e:
        print(f"Error executing command: {e}")
        
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except Exception as e:
                print(f"Warning: Failed to delete temporary image {temp_image_path}: {e}")
                
    return False, []

# --- 统一分发器入口 ---

def _extract_goods_from_single_image(catalog: dict, config: dict) -> tuple[bool, list[dict]]:
    """原单图处理与归一化逻辑，仅对 catalog 中的单张图片进行解析"""
    # 兼容历史的 openai_config 传参方式
    if "api_key" in config and "image_recognition" not in config:
        provider = "openai"
        openai_config = config
        cmd_config = {}
    else:
        ir_config = config.get("image_recognition", {})
        provider = ir_config.get("provider", "openai")
        openai_config = config.get("openai", {})
        cmd_config = ir_config.get("cmd", {})
        
    # 分发至对应识别引擎
    if provider == "openai":
        is_catalog, raw_items = extract_goods_via_openai(catalog, openai_config)
    elif provider == "cmd":
        is_catalog, raw_items = extract_goods_via_cmd(catalog, cmd_config, config)
    else:
        raise ValueError(f"Unknown image recognition provider: {provider}")
        
    if not is_catalog:
        return False, []
        
    # 通用后处理逻辑，格式化并映射回数据库所需字典列表
    extracted_items = []
    for item in raw_items:
        if isinstance(item, dict):
            normalized = fuzzy_normalize_item(item)
        else:
            name = getattr(item, "name", "")
            item_type = getattr(item, "type", "")
            price = getattr(item, "price", 0)
            is_set = getattr(item, "is_set", False)
            normalized = fuzzy_normalize_item({
                "name": name,
                "type": item_type,
                "price": price,
                "is_set": is_set
            })
        
        extracted_items.append({
            "circle_id": catalog["circle_id"],
            "catalog_id": catalog["id"],
            "name": normalized["name"],
            "type": normalized["type"],
            "price": normalized["price"],
            "is_set": 1 if normalized["is_set"] else 0,
            "raw_json": json.dumps(normalized, ensure_ascii=False)
        })
        
    return True, extracted_items

def extract_goods_from_catalog(catalog: dict, config: dict) -> tuple[bool, list[dict]]:
    """主分发器入口，支持不同图像识别引擎，对多张图片分别串行处理并合并结果"""
    image_path = catalog.get("image_path", "")
    if not image_path:
        return False, []

    image_paths = image_path.split(",")
    all_goods = []
    has_any_catalog = False
    has_any_failed = False

    for path in image_paths:
        path = path.strip()
        if not path:
            continue

        single_catalog = catalog.copy()
        single_catalog["image_path"] = path

        try:
            is_catalog, goods_list = _extract_goods_from_single_image(single_catalog, config)
            if is_catalog:
                has_any_catalog = True
                if goods_list:
                    all_goods.extend(goods_list)
        except Exception as e:
            print(f"Error processing single image {path}: {e}")
            has_any_failed = True

    if all_goods:
        # 只要有任意一张图片成功提取出商品，即判定为品书并返回合并后的制品
        return True, all_goods
    elif has_any_failed:
        # 如果没有任何商品且有图片处理报错，抛出异常以把整个 catalog 状态标为 failed，等待下次重试
        raise Exception("One or more images failed during extraction.")
    elif has_any_catalog:
        # 判定是品书但没提出来任何商品
        return True, []
    else:
        # 所有图片都被判定为非品书（ignored）
        return False, []

def process_pending_catalogs(
    db_path: str = None,
    day_list: list[str] = None,
    hall_list: list[str] = None,
    circle_ids: list[int] = None,
    name_query: str = None
):
    """扫描数据库中指定或所有 pending 品书并调用 LLM 进行提取"""
    config = load_config()
    
    # 确定要过滤的社团 ID 集合
    # 如果指定了任何筛选条件，调用 get_filtered_circle_ids 获得符合条件的 ID 集合
    has_filter = any(x is not None for x in [day_list, hall_list, circle_ids, name_query])
    
    if has_filter:
        db_to_use = db_path if db_path else "data/comic_market.db"
        from src.db import get_filtered_circle_ids
        target_ids = get_filtered_circle_ids(day_list, hall_list, circle_ids, name_query, db_path=db_to_use)
        print(f"Applying filters. Found {len(target_ids)} matching circle(s) to process.")
        if not target_ids:
            print("No matching circles found. Skipping LLM extraction.")
            return
    else:
        target_ids = None
        
    pending_list = get_pending_catalogs(db_path=db_path, circle_ids=target_ids) if db_path else get_pending_catalogs(circle_ids=target_ids)
    print(f"Found {len(pending_list)} pending catalogs to extract.")
    
    success_count = 0
    ignored_count = 0
    failed_count = 0
    
    for catalog in pending_list:
        catalog_id = catalog["id"]
        try:
            is_catalog, goods_list = extract_goods_from_catalog(catalog, config)
            
            if not is_catalog:
                print(f"Catalog {catalog_id} was classified as non-catalog or failed parsing. Ignoring.")
                if db_path:
                    update_catalog_status(catalog_id, "ignored", db_path=db_path)
                else:
                    update_catalog_status(catalog_id, "ignored")
                ignored_count += 1
            else:
                if goods_list:
                    if db_path:
                        save_goods(goods_list, db_path=db_path)
                        update_catalog_status(catalog_id, "processed", db_path=db_path)
                    else:
                        save_goods(goods_list)
                        update_catalog_status(catalog_id, "processed")
                    print(f"Successfully extracted {len(goods_list)} goods from catalog {catalog_id}.")
                    success_count += 1
                else:
                    print(f"No goods items returned for catalog {catalog_id}.")
                    if db_path:
                        update_catalog_status(catalog_id, "failed", db_path=db_path)
                    else:
                        update_catalog_status(catalog_id, "failed")
                    failed_count += 1
        except Exception as e:
            print(f"Error processing catalog {catalog_id}: {e}")
            if db_path:
                update_catalog_status(catalog_id, "failed", db_path=db_path)
            else:
                update_catalog_status(catalog_id, "failed")
            failed_count += 1
            
    print(f"Extraction summary: {success_count} processed, {ignored_count} ignored, {failed_count} failed.")
