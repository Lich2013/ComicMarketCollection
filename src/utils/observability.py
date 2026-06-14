import os

# Global flag to track if langfuse tracing is successfully enabled
_LANGFUSE_ACTIVE = False

def init_observability(config: dict):
    """
    检查并初始化 Langfuse 可观测性。
    如果配置启用且自检成功，则启用链路追踪，否则友好降级。
    """
    global _LANGFUSE_ACTIVE
    
    langfuse_config = config.get("langfuse", {})
    enabled = langfuse_config.get("enabled", False)
    
    # 支持环境变量覆盖
    env_enabled = os.environ.get("LANGFUSE_ENABLED")
    if env_enabled is not None:
        enabled = env_enabled.lower() == "true"
        
    if not enabled:
        return
        
    host = langfuse_config.get("host") or os.environ.get("LANGFUSE_HOST") or "http://localhost:3000"
    public_key = langfuse_config.get("public_key") or os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = langfuse_config.get("secret_key") or os.environ.get("LANGFUSE_SECRET_KEY")
    
    # 注入环境变量供 langfuse.openai 内部初始化读取
    os.environ["LANGFUSE_HOST"] = host
    if public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
    if secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = secret_key
        
    try:
        # 防御性导入，防止 langfuse 缺失导致直接崩溃
        from langfuse import Langfuse
        
        # 连通性自检
        lf = Langfuse()
        if lf.auth_check():
            _LANGFUSE_ACTIVE = True
            print(f"\033[32m✅ [Observability] 成功连接到 Langfuse 服务 ({host})，LLM 链路追踪已启用！\033[0m")
        else:
            print(f"\033[33m⚠️ [Observability Warning] Langfuse 服务 ({host}) 连通性自检失败。系统已自动降级为原生模式，跳过链路追踪！\033[0m")
    except ImportError:
        print("\033[33m⚠️ [Observability Warning] 未检测到 `langfuse` 依赖包。系统已自动降级为原生模式，跳过链路追踪！\033[0m")
    except Exception as e:
        print(f"\033[33m⚠️ [Observability Warning] 链路追踪检测异常: {e}。系统已自动降级为原生模式，跳过链路追踪！\033[0m")

def is_langfuse_active() -> bool:
    """查询当前 Langfuse 链路追踪是否开启"""
    return _LANGFUSE_ACTIVE

def get_openai_client(api_key: str, base_url: str):
    """
    根据 Langfuse 的激活状态，返回合适的 OpenAI Client。
    如果是激活状态，返回 `from langfuse.openai import OpenAI`。
    否则返回原生 `from openai import OpenAI`。
    """
    if _LANGFUSE_ACTIVE:
        try:
            from langfuse.openai import OpenAI
            return OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            # 极速降级防御
            print(f"\033[33m⚠️ [Observability Warning] 无法实例化 Langfuse OpenAI 客户端: {e}。已降级为原生 OpenAI 客户端。\033[0m")
            from openai import OpenAI
            return OpenAI(api_key=api_key, base_url=base_url)
    else:
        from openai import OpenAI
        return OpenAI(api_key=api_key, base_url=base_url)
