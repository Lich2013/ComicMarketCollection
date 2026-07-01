import requests
import re
import sys
from html.parser import HTMLParser
from src.db import save_comiket_genre_mappings, init_db, DEFAULT_DB_PATH

def clean_int(val_str):
    if not val_str:
        return 1
    # 提取所有数字
    digits = re.sub(r'\D', '', str(val_str))
    return int(digits) if digits else 1

class ComiketGenreParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_tr = False
        self.in_td = False
        self.in_th = False
        self.current_row = []
        self.current_cell = ""
        self.table_data = []
        self.td_attrs = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "table" and attrs_dict.get("class") == "table_0":
            self.in_table = True
        elif self.in_table:
            if tag == "tr":
                self.in_tr = True
                self.current_row = []
            elif tag in ("td", "th") and self.in_tr:
                self.in_td = (tag == "td")
                self.in_th = (tag == "th")
                self.current_cell = ""
                self.td_attrs = attrs_dict

    def handle_data(self, data):
        if self.in_table and self.in_tr and (self.in_td or self.in_th):
            self.current_cell += data

    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            self.in_table = False
        elif self.in_table:
            if tag == "tr" and self.in_tr:
                self.in_tr = False
                self.table_data.append(self.current_row)
            elif tag in ("td", "th") and (self.in_td or self.in_th):
                cell_text = self.current_cell.strip()
                rowspan = clean_int(self.td_attrs.get("rowspan", 1))
                colspan = clean_int(self.td_attrs.get("colspan", 1))
                is_th = self.in_th
                self.in_td = False
                self.in_th = False
                self.current_row.append({
                    "text": cell_text,
                    "rowspan": rowspan,
                    "colspan": colspan,
                    "is_th": is_th,
                    "class": self.td_attrs.get("class", "")
                })

def reconstruct_table(table_data):
    occupied = {}
    for r_idx, row in enumerate(table_data):
        c_idx = 0
        for cell in row:
            while (r_idx, c_idx) in occupied:
                c_idx += 1
            rowspan = cell["rowspan"]
            colspan = cell["colspan"]
            text = cell["text"]
            for dr in range(rowspan):
                for dc in range(colspan):
                    occupied[(r_idx + dr, c_idx + dc)] = {
                        "text": text,
                        "class": cell["class"],
                        "is_th": cell["is_th"]
                    }
            c_idx += colspan
            
    max_row = max(r for r, c in occupied.keys()) if occupied else -1
    max_col = max(c for r, c in occupied.keys()) if occupied else -1
    
    reconstructed = []
    for r in range(max_row + 1):
        row_list = []
        for c in range(max_col + 1):
            row_list.append(occupied.get((r, c), {"text": "", "class": "", "is_th": False}))
        reconstructed.append(row_list)
    return reconstructed

def import_c108_genre_mapping(db_path: str = DEFAULT_DB_PATH) -> bool:
    """抓取官方 C108 题材对照表并解析导入数据库"""
    # 确保数据库表已初始化
    init_db(db_path)
    
    url = "https://www.comiket.co.jp/info-c/C108/C108genre.html"
    print(f"Fetching C108 genre mapping table from: {url}...")
    
    try:
        response = requests.get(url, timeout=30)
        # Comiket 官方一般是 ISO-2022-JP 编码，若不显式指定可能乱码
        response.encoding = 'iso-2022-jp'
        html_content = response.text
        
        parser = ComiketGenreParser()
        parser.feed(html_content)
        
        if not parser.table_data:
            print("Error: Could not find table rows in table_0 class table.")
            return False
            
        reconstructed = reconstruct_table(parser.table_data)
        
        mappings = []
        for row in reconstructed:
            # 跳过表头
            if not row or row[0]["is_th"]:
                continue
                
            # 官方表格一般包含 5 列: 日期, 编码, 类别名称, 备注说明, 补足说明
            if len(row) < 5:
                continue
                
            day_text = row[0]["text"]
            code_text = row[1]["text"]
            name_text = row[2]["text"]
            note_text = row[3]["text"]
            supplement_text = row[4]["text"]
            
            # 转换 code 为整型
            try:
                code = int(code_text)
            except ValueError:
                # 忽略无法转换为整数的表头或特殊行
                continue
                
            mappings.append({
                "event": "C108",
                "day": day_text,
                "genre_code": code,
                "genre_name": name_text,
                "note": note_text if note_text else None,
                "supplement": supplement_text if supplement_text else None
            })
            
        if not mappings:
            print("No valid genre mappings parsed.")
            return False
            
        print(f"Successfully parsed {len(mappings)} genre items. Committing to DB...")
        save_comiket_genre_mappings(mappings, db_path=db_path)
        print(f"Successfully imported {len(mappings)} C108 genre items into DB.")
        return True
        
    except Exception as e:
        print(f"Error importing C108 genres: {e}", file=sys.stderr)
        return False
