import io
import json
import base64
from PIL import Image
from pydantic import BaseModel, Field
from openai import OpenAI

from src.db import get_pending_catalogs, save_goods, update_catalog_status
from src.config import load_config

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

# --- 核心提取逻辑 ---

def extract_goods_from_catalog(catalog: dict, openai_config: dict) -> tuple[bool, list[dict]]:
    """调用 OpenAI 多模态 API 解析单张品书图"""
    image_path = catalog.get("image_path")
    circle_name = catalog.get("circle_name", "未知社团")
    
    print(f"Extracting goods from catalog image for {circle_name}: {image_path}")
    
    api_key = openai_config.get("api_key")
    base_url = openai_config.get("base_url")
    model = openai_config.get("model", "gpt-4o-mini")
    
    if not api_key:
        raise ValueError("OpenAI API key is missing. Please set OPENAI_API_KEY environment variable or configure config.yaml.")
        
    client = OpenAI(api_key=api_key, base_url=base_url)
    
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
        if not result:
            print("Failed to get parsed structure from LLM.")
            return False, []
            
        if not result.is_catalog:
            print("LLM classified this image as NOT a catalog sheet.")
            return False, []
            
        extracted_items = []
        for item in result.items:
            extracted_items.append({
                "circle_id": catalog["circle_id"],
                "catalog_id": catalog["id"],
                "name": item.name,
                "type": item.type,
                "price": item.price,
                "is_set": 1 if item.is_set else 0,
                "raw_json": json.dumps(item.model_dump(), ensure_ascii=False)
            })
            
        return True, extracted_items
        
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
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
    openai_config = config["openai"]
    
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
            is_catalog, goods_list = extract_goods_from_catalog(catalog, openai_config)
            
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
