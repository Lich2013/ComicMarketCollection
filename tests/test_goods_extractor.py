import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.config import load_config
from src.goods_extractor import (
    clean_price, clean_boolean, fuzzy_normalize_item,
    parse_json_from_stdout, try_parse_markdown_list,
    extract_goods_from_catalog
)

def test_config_image_recognition_default():
    config = load_config()
    assert "image_recognition" in config
    assert config["image_recognition"]["provider"] in ("openai", "cmd")

def test_clean_price():
    assert clean_price(1000) == 1000
    assert clean_price("1,000円") == 1000
    assert clean_price("¥500") == 500
    assert clean_price(None) == 0
    assert clean_price("免费") == 0
    assert clean_price("500") == 500

def test_clean_boolean():
    assert clean_boolean(True) is True
    assert clean_boolean(False) is False
    assert clean_boolean("yes") is True
    assert clean_boolean("NO") is False
    assert clean_boolean("1") is True
    assert clean_boolean("0") is False
    assert clean_boolean("套装") is True

def test_fuzzy_normalize_item():
    raw1 = {"title": "新刊A", "cost": "¥1,000", "set": "yes"}
    norm1 = fuzzy_normalize_item(raw1)
    assert norm1["name"] == "新刊A"
    assert norm1["price"] == 1000
    assert norm1["is_set"] is True
    
    raw2 = {"name": "既刊B", "price": 500}
    norm2 = fuzzy_normalize_item(raw2)
    assert norm2["name"] == "既刊B"
    assert norm2["price"] == 500
    assert norm2["is_set"] is False

    raw3 = {"book": "新刊新刊セット", "yen": "2000"}
    norm3 = fuzzy_normalize_item(raw3)
    assert norm3["name"] == "新刊新刊セット"
    assert norm3["price"] == 2000
    assert norm3["is_set"] is True

def test_parse_json_from_stdout():
    # Markdown format
    text1 = """
    Some pre-text
    ```json
    {
      "is_catalog": true,
      "items": [
        {"name": "新刊 A", "price": 1000}
      ]
    }
    ```
    Post text
    """
    success, is_cat, items = parse_json_from_stdout(text1)
    assert success is True
    assert is_cat is True
    assert len(items) == 1
    assert items[0]["name"] == "新刊 A"

    # Plain list output
    text2 = '[{"name": "Item B", "price": 500}]'
    success2, is_cat2, items2 = parse_json_from_stdout(text2)
    assert success2 is True
    assert is_cat2 is True
    assert len(items2) == 1
    assert items2[0]["name"] == "Item B"

def test_try_parse_markdown_list():
    text = """
    - 新刊 A - 1000円
    * 既刊 B : 500
    + 新刊套装 ￥2,000
    """
    items = try_parse_markdown_list(text)
    assert len(items) == 3
    assert items[0]["name"] == "新刊 A"
    assert items[0]["price"] == 1000
    assert items[0]["is_set"] is False
    
    assert items[1]["name"] == "既刊 B"
    assert items[1]["price"] == 500
    assert items[1]["is_set"] is False

    assert items[2]["name"] == "新刊套装"
    assert items[2]["price"] == 2000
    assert items[2]["is_set"] is True

@patch("src.goods_extractor.subprocess.run")
def test_extract_goods_via_cmd_success(mock_run):
    mock_response = MagicMock()
    mock_response.returncode = 0
    mock_response.stdout = """
    {
      "is_catalog": true,
      "items": [
        {"title": "新刊 A", "cost": "1000"}
      ]
    }
    """
    mock_run.return_value = mock_response

    catalog = {
        "id": 1,
        "circle_id": 123,
        "image_path": "data/images/123/img.jpg",
        "circle_name": "Test Circle",
        "circle_author": "Test Author"
    }

    config = {
        "image_recognition": {
            "provider": "cmd",
            "cmd": {
                "command": "some-cli",
                "args": ["-p", "{prompt}"],
                "timeout": 30,
                "fallback_text_formatter": False
            }
        }
    }

    success, items = extract_goods_from_catalog(catalog, config)
    assert success is True
    assert len(items) == 1
    assert items[0]["name"] == "新刊 A"
    assert items[0]["price"] == 1000
    assert items[0]["is_set"] == 0
    assert items[0]["circle_id"] == 123
