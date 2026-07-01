import os
import json
import pytest
from unittest.mock import MagicMock, patch
from src.twitter_sync import (
    validate_cookies,
    save_cookies_to_file,
    scrape_twitter_profile,
    scrape_single_tweet
)


def test_validate_cookies():
    # 正常含 auth_token 的 cookie 校验通过
    assert validate_cookies([{"name": "auth_token", "value": "valid_token"}]) is True
    # 包含其他字段但没有 auth_token 校验失败
    assert validate_cookies([{"name": "ct0", "value": "csrf_token"}]) is False
    # 含有 auth_token 但值为空校验失败
    assert validate_cookies([{"name": "auth_token", "value": ""}]) is False
    # 空列表校验失败
    assert validate_cookies([]) is False
    assert validate_cookies(None) is False


def test_save_cookies_to_file(tmp_path):
    cookie_file = tmp_path / "test_cookies.json"
    test_cookies = [{"name": "auth_token", "value": "test_token", "domain": ".x.com"}]
    
    # 测试写入
    save_cookies_to_file(test_cookies, str(cookie_file))
    
    # 验证文件是否存在且内容一致
    assert cookie_file.exists()
    with open(cookie_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == test_cookies


@patch("src.twitter_sync.sync_playwright")
def test_scrape_twitter_profile_success(mock_playwright, tmp_path):
    # Mock Playwright 的 context.cookies() 和 page.url
    cookie_file = tmp_path / "test_cookies.json"
    initial_cookies = [{"name": "auth_token", "value": "old_token"}]
    with open(cookie_file, "w", encoding="utf-8") as f:
        json.dump(initial_cookies, f)
        
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_browser = MagicMock()
    
    # 配置 mock 行为
    mock_page.url = "https://x.com/test_user"
    mock_context.new_page.return_value = mock_page
    
    # 模拟更新后的 cookies
    refreshed_cookies = [{"name": "auth_token", "value": "new_token"}]
    mock_context.cookies.return_value = refreshed_cookies
    
    mock_browser.new_context.return_value = mock_context
    
    # 配置 sync_playwright 启动上下文
    mock_p_instance = MagicMock()
    mock_p_instance.chromium.launch.return_value = mock_browser
    mock_playwright.return_value.__enter__.return_value = mock_p_instance
    
    # 执行 profile 抓取
    scrape_twitter_profile("test_user", cookies=initial_cookies, cookies_file=str(cookie_file))
    
    # 验证是否正确触发了 cookies 回写
    assert cookie_file.exists()
    with open(cookie_file, "r", encoding="utf-8") as f:
        saved_cookies = json.load(f)
    assert saved_cookies == refreshed_cookies


@patch("src.twitter_sync.sync_playwright")
def test_scrape_twitter_profile_login_redirection(mock_playwright, tmp_path):
    # 测试如果被重定向到 login 页面，则不进行覆写
    cookie_file = tmp_path / "test_cookies.json"
    initial_cookies = [{"name": "auth_token", "value": "old_token"}]
    with open(cookie_file, "w", encoding="utf-8") as f:
        json.dump(initial_cookies, f)
        
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_browser = MagicMock()
    
    # 模拟重定向至登录流程
    mock_page.url = "https://x.com/i/flow/login"
    mock_context.new_page.return_value = mock_page
    
    # 即使 context 返回了某些残留/无效 cookie
    refreshed_cookies = [{"name": "auth_token", "value": ""}]
    mock_context.cookies.return_value = refreshed_cookies
    
    mock_browser.new_context.return_value = mock_context
    
    mock_p_instance = MagicMock()
    mock_p_instance.chromium.launch.return_value = mock_browser
    mock_playwright.return_value.__enter__.return_value = mock_p_instance
    
    # 执行抓取
    scrape_twitter_profile("test_user", cookies=initial_cookies, cookies_file=str(cookie_file))
    
    # 验证文件内容没有被修改，依然是 old_token
    with open(cookie_file, "r", encoding="utf-8") as f:
        saved_cookies = json.load(f)
    assert saved_cookies == initial_cookies


@patch("src.twitter_sync.sync_playwright")
def test_scrape_single_tweet_success(mock_playwright, tmp_path):
    cookie_file = tmp_path / "test_cookies.json"
    initial_cookies = [{"name": "auth_token", "value": "old_token"}]
    with open(cookie_file, "w", encoding="utf-8") as f:
        json.dump(initial_cookies, f)
        
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_browser = MagicMock()
    
    mock_page.url = "https://x.com/test_user/status/12345"
    mock_context.new_page.return_value = mock_page
    
    refreshed_cookies = [{"name": "auth_token", "value": "new_token_single"}]
    mock_context.cookies.return_value = refreshed_cookies
    
    mock_browser.new_context.return_value = mock_context
    mock_p_instance = MagicMock()
    mock_p_instance.chromium.launch.return_value = mock_browser
    mock_playwright.return_value.__enter__.return_value = mock_p_instance
    
    # 执行单推抓取
    scrape_single_tweet("https://x.com/test_user/status/12345", cookies=initial_cookies, cookies_file=str(cookie_file))
    
    # 验证是否正确更新
    with open(cookie_file, "r", encoding="utf-8") as f:
        saved_cookies = json.load(f)
    assert saved_cookies == refreshed_cookies
