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
    cmd_cfg = config["image_recognition"]["cmd"]
    # Check default pre-compression config values
    assert "compress" in cmd_cfg
    assert cmd_cfg["compress"] is False
    assert cmd_cfg["max_size"] == 1500
    assert cmd_cfg["quality"] == 85

def test_config_image_recognition_env_overrides():
    with patch.dict(os.environ, {
        "IMAGE_RECOGNITION_CMD_COMPRESS": "true",
        "IMAGE_RECOGNITION_CMD_MAX_SIZE": "2000",
        "IMAGE_RECOGNITION_CMD_QUALITY": "90"
    }):
        config = load_config()
        cmd_cfg = config["image_recognition"]["cmd"]
        assert cmd_cfg["compress"] is True
        assert cmd_cfg["max_size"] == 2000
        assert cmd_cfg["quality"] == 90

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

@patch("src.goods_extractor._extract_goods_from_single_image")
def test_extract_goods_multiple_images(mock_extract_single):
    mock_extract_single.side_effect = [
        (True, [{"circle_id": 123, "catalog_id": 1, "name": "Item A", "type": "新刊", "price": 1000, "is_set": 0, "raw_json": "{}"}]),
        (True, [{"circle_id": 123, "catalog_id": 1, "name": "Item B", "type": "周边", "price": 500, "is_set": 0, "raw_json": "{}"}])
    ]
    
    catalog = {
        "id": 1,
        "circle_id": 123,
        "image_path": "path1.jpg,path2.jpg",
        "circle_name": "Test Circle",
        "circle_author": "Test Author"
    }
    config = {}
    
    success, items = extract_goods_from_catalog(catalog, config)
    assert success is True
    assert len(items) == 2
    assert items[0]["name"] == "Item A"
    assert items[1]["name"] == "Item B"

@patch("src.goods_extractor.subprocess.run")
@patch("src.goods_extractor.os.path.exists")
@patch("src.goods_extractor.os.path.getsize")
@patch("src.goods_extractor.Image.open")
def test_extract_goods_via_cmd_compression(mock_image_open, mock_getsize, mock_exists, mock_run):
    # Setup mocks
    mock_exists.side_effect = lambda path: True
    
    # original image size = 1,000,000 bytes (1MB)
    # compressed image size = 300,000 bytes (300KB)
    mock_getsize.side_effect = lambda path: 300000 if "tmp" in path else 1000000
    
    mock_img = MagicMock()
    mock_img.size = (2000, 1000)  # max side 2000 > max_size 1500
    mock_img.mode = "RGB"
    mock_resized_img = MagicMock()
    mock_resized_img.size = (1500, 750)
    mock_img.resize.return_value = mock_resized_img
    mock_image_open.return_value.__enter__.return_value = mock_img
    
    mock_response = MagicMock()
    mock_response.returncode = 0
    mock_response.stdout = '{"is_catalog": true, "items": [{"title": "Compressed A", "cost": "500"}]}'
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
                "args": ["-p", "{prompt}", "-i", "{image_path}"],
                "timeout": 30,
                "fallback_text_formatter": False,
                "compress": True,
                "max_size": 1500,
                "quality": 80
            }
        }
    }

    # Track if temp file is deleted
    deleted_files = []
    with patch("src.goods_extractor.os.remove", side_effect=deleted_files.append) as mock_remove:
        success, items = extract_goods_from_catalog(catalog, config)
        
        # Verify success
        assert success is True
        assert len(items) == 1
        assert items[0]["name"] == "Compressed A"
        
        # Verify resize was called
        mock_img.resize.assert_called_once()
        
        # Verify temp file was saved
        mock_resized_img.save.assert_called_once()
        
        # Verify command argument was replaced with temp file path
        called_args = mock_run.call_args[0][0]
        # Look for the -i argument value
        img_idx = called_args.index("-i")
        temp_img_path = called_args[img_idx + 1]
        assert "tmp_" in temp_img_path
        assert temp_img_path.endswith(".jpg")
        
        # Verify temporary file deletion was triggered in finally
        assert temp_img_path in deleted_files

@patch("src.goods_extractor.subprocess.run")
@patch("src.goods_extractor.os.path.exists")
@patch("src.goods_extractor.os.path.getsize")
@patch("src.goods_extractor.Image.open")
def test_extract_goods_via_cmd_compression_fallback(mock_image_open, mock_getsize, mock_exists, mock_run):
    # Setup mocks
    mock_exists.side_effect = lambda path: True
    
    # original image size = 300,000 bytes (300KB)
    # compressed image size = 290,000 bytes (290KB) -> 290/300 = 96.6% >= 90%, should fallback!
    mock_getsize.side_effect = lambda path: 290000 if "tmp" in path else 300000
    
    mock_img = MagicMock()
    mock_img.size = (1522, 1076)
    mock_img.mode = "RGB"
    mock_resized_img = MagicMock()
    mock_resized_img.size = (1500, 1060)
    mock_img.resize.return_value = mock_resized_img
    mock_image_open.return_value.__enter__.return_value = mock_img
    
    mock_response = MagicMock()
    mock_response.returncode = 0
    mock_response.stdout = '{"is_catalog": true, "items": [{"title": "Fallback A", "cost": "800"}]}'
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
                "args": ["-p", "{prompt}", "-i", "{image_path}"],
                "timeout": 30,
                "fallback_text_formatter": False,
                "compress": True,
                "max_size": 1500,
                "quality": 85
            }
        }
    }

    deleted_files = []
    with patch("src.goods_extractor.os.remove", side_effect=deleted_files.append) as mock_remove:
        success, items = extract_goods_from_catalog(catalog, config)
        
        # Verify success
        assert success is True
        assert len(items) == 1
        assert items[0]["name"] == "Fallback A"
        
        # Verify command argument was replaced with ORIGINAL file path, not temp path
        called_args = mock_run.call_args[0][0]
        img_idx = called_args.index("-i")
        image_arg = called_args[img_idx + 1]
        assert image_arg == "data/images/123/img.jpg"
        
        # Verify the temp file was still deleted immediately when fallback occurred
        assert any("tmp_" in f for f in deleted_files)


