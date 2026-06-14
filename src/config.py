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
            "cookie_string": os.environ.get("TWITTER_COOKIE_STRING", ""),
            "since_date": os.environ.get("TWITTER_SINCE_DATE", ""),
            "until_date": os.environ.get("TWITTER_UNTIL_DATE", "")
        },
        "openai": {
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        },
        "tweet_analysis": {
            "enabled": os.environ.get("TWEET_ANALYSIS_ENABLED", "false").lower() == "true",
            "api_key": os.environ.get("TWEET_ANALYSIS_API_KEY", ""),
            "base_url": os.environ.get("TWEET_ANALYSIS_BASE_URL", ""),
            "model": os.environ.get("TWEET_ANALYSIS_MODEL", "")
        },
        "image_recognition": {
            "provider": os.environ.get("IMAGE_RECOGNITION_PROVIDER", "openai"),
            "cmd": {
                "command": os.environ.get("IMAGE_RECOGNITION_CMD", "agy"),
                "args": ["-p", "{prompt}"],
                "timeout": int(os.environ.get("IMAGE_RECOGNITION_CMD_TIMEOUT", "180")),
                "fallback_text_formatter": os.environ.get("IMAGE_RECOGNITION_FALLBACK_TEXT_FORMATTER", "true").lower() == "true"
            }
        },
        "langfuse": {
            "enabled": os.environ.get("LANGFUSE_ENABLED", "false").lower() == "true",
            "host": os.environ.get("LANGFUSE_HOST", "http://localhost:3000"),
            "public_key": os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
            "secret_key": os.environ.get("LANGFUSE_SECRET_KEY", "")
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
    if os.environ.get("TWITTER_SINCE_DATE"):
        config["twitter"]["since_date"] = os.environ.get("TWITTER_SINCE_DATE")
    if os.environ.get("TWITTER_UNTIL_DATE"):
        config["twitter"]["until_date"] = os.environ.get("TWITTER_UNTIL_DATE")
    if os.environ.get("OPENAI_API_KEY"):
        config["openai"]["api_key"] = os.environ.get("OPENAI_API_KEY")
    if os.environ.get("OPENAI_BASE_URL"):
        config["openai"]["base_url"] = os.environ.get("OPENAI_BASE_URL")
    if os.environ.get("OPENAI_MODEL"):
        config["openai"]["model"] = os.environ.get("OPENAI_MODEL")
        
    if os.environ.get("TWEET_ANALYSIS_ENABLED"):
        config["tweet_analysis"]["enabled"] = os.environ.get("TWEET_ANALYSIS_ENABLED").lower() == "true"
    if os.environ.get("TWEET_ANALYSIS_API_KEY"):
        config["tweet_analysis"]["api_key"] = os.environ.get("TWEET_ANALYSIS_API_KEY")
    if os.environ.get("TWEET_ANALYSIS_BASE_URL"):
        config["tweet_analysis"]["base_url"] = os.environ.get("TWEET_ANALYSIS_BASE_URL")
    if os.environ.get("TWEET_ANALYSIS_MODEL"):
        config["tweet_analysis"]["model"] = os.environ.get("TWEET_ANALYSIS_MODEL")
        
    if os.environ.get("IMAGE_RECOGNITION_PROVIDER"):
        config["image_recognition"]["provider"] = os.environ.get("IMAGE_RECOGNITION_PROVIDER")
    if os.environ.get("IMAGE_RECOGNITION_CMD"):
        config["image_recognition"]["cmd"]["command"] = os.environ.get("IMAGE_RECOGNITION_CMD")
    if os.environ.get("IMAGE_RECOGNITION_CMD_TIMEOUT"):
        try:
            config["image_recognition"]["cmd"]["timeout"] = int(os.environ.get("IMAGE_RECOGNITION_CMD_TIMEOUT"))
        except ValueError:
            pass
    if os.environ.get("IMAGE_RECOGNITION_FALLBACK_TEXT_FORMATTER"):
        config["image_recognition"]["cmd"]["fallback_text_formatter"] = os.environ.get("IMAGE_RECOGNITION_FALLBACK_TEXT_FORMATTER").lower() == "true"
        
    if os.environ.get("LANGFUSE_ENABLED"):
        config["langfuse"]["enabled"] = os.environ.get("LANGFUSE_ENABLED").lower() == "true"
    if os.environ.get("LANGFUSE_HOST"):
        config["langfuse"]["host"] = os.environ.get("LANGFUSE_HOST")
    if os.environ.get("LANGFUSE_PUBLIC_KEY"):
        config["langfuse"]["public_key"] = os.environ.get("LANGFUSE_PUBLIC_KEY")
    if os.environ.get("LANGFUSE_SECRET_KEY"):
        config["langfuse"]["secret_key"] = os.environ.get("LANGFUSE_SECRET_KEY")

    # 智能回退策略（按字段独立 fallback）
    analysis = config["tweet_analysis"]
    openai = config["openai"]
    if not analysis.get("api_key"):
        analysis["api_key"] = openai.get("api_key")
    if not analysis.get("base_url"):
        analysis["base_url"] = openai.get("base_url")
    if not analysis.get("model"):
        analysis["model"] = openai.get("model")
        
    return config

def write_default_config(config_path: str = DEFAULT_CONFIG_PATH):
    """写入默认配置模版 file"""
    default_template = {
        "webcatalog": {
            "cookie": "AspNet.Consent=yes; .ASPXAUTH=CF6489D5F8...",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        "twitter": {
            "cookies_file": "data/twitter_cookies.json",
            "cookie_string": "",
            "since_date": "2026-06-01",
            "until_date": "2026-06-05"
        },
        "openai": {
            "api_key": "your-openai-api-key-here",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        },
        "tweet_analysis": {
            "enabled": False,
            "api_key": "your-analysis-api-key-here",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        },
        "image_recognition": {
            "provider": "openai",
            "cmd": {
                "command": "agy",
                "args": ["-p", "{prompt}"],
                "timeout": 180,
                "fallback_text_formatter": True
            }
        },
        "langfuse": {
            "enabled": False,
            "host": "http://localhost:3000",
            "public_key": "pk-lf-your-public-key-here",
            "secret_key": "sk-lf-your-secret-key-here"
        }
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(default_template, f, default_flow_style=False, allow_unicode=True)
