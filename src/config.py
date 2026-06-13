import os
import yaml

DEFAULT_CONFIG_PATH = "config.yaml"

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    """加载配置文件，若不存在则返回包含默认/环境变量的字典"""
    config = {
        "webcatalog": {
            "cookie": os.environ.get("WEBCATALOG_COOKIE", ""),
            "user_agent": os.environ.get(
                "WEBCATALOG_USER_AGENT", 
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        },
        "twitter": {
            "cookies_file": os.environ.get("TWITTER_COOKIES_FILE", "data/twitter_cookies.json"),
            "cookie_string": os.environ.get("TWITTER_COOKIE_STRING", "")
        },
        "openai": {
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        }
    }
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                user_config = yaml.safe_load(f) or {}
                # 递归更新字典
                for key, val in user_config.items():
                    if isinstance(val, dict) and key in config:
                        config[key].update(val)
                    else:
                        config[key] = val
            except Exception as e:
                print(f"Error parsing config.yaml: {e}")
                
    # 环境变量优先级最高
    if os.environ.get("WEBCATALOG_COOKIE"):
        config["webcatalog"]["cookie"] = os.environ.get("WEBCATALOG_COOKIE")
    if os.environ.get("WEBCATALOG_USER_AGENT"):
        config["webcatalog"]["user_agent"] = os.environ.get("WEBCATALOG_USER_AGENT")
    if os.environ.get("TWITTER_COOKIES_FILE"):
        config["twitter"]["cookies_file"] = os.environ.get("TWITTER_COOKIES_FILE")
    if os.environ.get("TWITTER_COOKIE_STRING"):
        config["twitter"]["cookie_string"] = os.environ.get("TWITTER_COOKIE_STRING")
    if os.environ.get("OPENAI_API_KEY"):
        config["openai"]["api_key"] = os.environ.get("OPENAI_API_KEY")
    if os.environ.get("OPENAI_BASE_URL"):
        config["openai"]["base_url"] = os.environ.get("OPENAI_BASE_URL")
    if os.environ.get("OPENAI_MODEL"):
        config["openai"]["model"] = os.environ.get("OPENAI_MODEL")
        
    return config

def write_default_config(config_path: str = DEFAULT_CONFIG_PATH):
    """写入默认配置模版文件"""
    default_template = {
        "webcatalog": {
            "cookie": "AspNet.Consent=yes; .ASPXAUTH=CF6489D5F8...",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        "twitter": {
            "cookies_file": "data/twitter_cookies.json",
            "cookie_string": ""
        },
        "openai": {
            "api_key": "your-openai-api-key-here",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        }
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(default_template, f, default_flow_style=False, allow_unicode=True)
