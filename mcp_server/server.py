"""
TrendRadar MCP Server - FastMCP 2.0 实现

使用 FastMCP 2.0 提供生产级 MCP 工具服务器。
支持 stdio 和 HTTP 两种传输模式。
"""

import os
import json
from typing import List, Optional, Dict

from starlette.requests import Request
from starlette.responses import JSONResponse
from fastmcp import FastMCP

from .tools.data_query import DataQueryTools
from .tools.analytics import AnalyticsTools
from .tools.search_tools import SearchTools
from .tools.config_mgmt import ConfigManagementTools
from .tools.system import SystemManagementTools


# 创建 FastMCP 2.0 应用
mcp = FastMCP('trendradar-news')

# 从环境变量读取预设的密码
# 这个密码由 start-http.bat 或 start-http.sh 脚本设置
SERVER_PASSWORD = os.getenv("MCP_SERVER_PASSWORD")


async def authentication_middleware(request: Request, call_next):
    """
    密码认证中间件 - 验证HTTP请求中的密码
    
    仅在HTTP模式下生效。当MCP_SERVER_PASSWORD环境变量被设置时，
    所有请求都必须在URL查询参数中提供正确的密码，否则返回403错误。
    
    密码可以通过以下方式传递：
    - URL查询参数：http://localhost:3333/mcp?pwd=<password>
    - X-MCP-Password请求头：curl -H "X-MCP-Password: <password>" http://localhost:3333/mcp
    """
    # 仅当服务器设置了密码时才启用验证
    if SERVER_PASSWORD:
        # 优先尝试从请求头获取密码
        password_from_header = request.headers.get("X-MCP-Password")
        
        # 其次从URL查询参数获取密码
        password_from_query = request.query_params.get("pwd")
        
        # 获取客户端提供的密码（优先使用请求头）
        client_password = password_from_header or password_from_query
        
        # 如果密码不正确或未提供，则返回 403 Forbidden 错误
        if client_password != SERVER_PASSWORD:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "message": "Invalid or missing password. Please provide 'pwd' query parameter or 'X-MCP-Password' header."
                },
            )
    
    # 如果密码正确或服务器未设置密码，则继续处理请求
    response = await call_next(request)
    return response


# 注册认证中间件
mcp.add_middleware(authentication_middleware)

# 全局工具实例（在第一次请求时初始化）
_tools_instances = {}


def _get_tools(project_root: Optional[str] = None):
    """获取或创建工具实例（单例模式）"""
    if not _tools_instances:
        _tools_instances['data'] = DataQueryTools(project_root)
        _tools_instances['analytics'] = AnalyticsTools(project_root)
        _tools_instances['search'] = SearchTools(project_root)
        _tools_instances['config'] = ConfigManagementTools(project_root)
        _tools_instances['system'] = SystemManagementTools(project_root)
    return _tools_instances


# ==================== 数据查询工具 ====================

@mcp.tool
async def get_latest_news(
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    获取最新一批爬取的新闻数据，快速了解当前热点

    Args:
        platforms: 平台ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定时：使用 config.yaml 中配置的所有平台
                   - 支持的平台来自 config/config.yaml 的 platforms 配置
                   - 每个平台都有对应的name字段（如"知乎"、"微博"），方便AI识别
        limit: 返回条数限制，默认50，最大1000
               注意：实际返回数量可能少于请求值，取决于当前可用的新闻总数
        include_url: 是否包含URL链接，默认False（节省token）

    Returns:
        JSON格式的新闻列表

    **重要：数据展示建议**
    本工具会返回完整的新闻列表（通常50条）给你。但请注意：
    - **工具返回**：完整的50条数据 ✅
    - **建议展示**：向用户展示全部数据，除非用户明确要求总结
    - **用户期望**：用户可能需要完整数据，请谨慎总结

    **何时可以总结**：
    - 用户明确说"给我总结一下"或"挑重点说"
    - 数据量超过100条时，可先展示部分并询问是否查看全部

    **注意**：如果用户询问"为什么只显示了部分"，说明他们需要完整数据
    """
    tools = _get_tools()
    result = tools['data'].get_latest_news(platforms=platforms, limit=limit, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_trending_topics(
    top_n: int = 10,
    mode: str = 'current'
) -> str:
    """
    获取个人关注词的新闻出现频率统计（基于 config/frequency_words.txt）

    注意：本工具不是自动提取新闻热点，而是统计你在 config/frequency_words.txt 中
    设置的个人关注词在新闻中出现的频率。你可以自定义这个关注词列表。

    Args:
        top_n: 返回TOP N关注词，默认10
        mode: 模式选择
            - daily: 当日累计数据统计
            - current: 最新一批数据统计（默认）

    Returns:
        JSON格式的关注词频率统计列表
    """
    tools = _get_tools()
    result = tools['data'].get_trending_topics(top_n=top_n, mode=mode)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_news_by_date(
    date_query: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    获取指定日期的新闻数据，用于历史数据分析和对比

    Args:
        date_query: 日期查询，可选格式:
            - 自然语言: "今天", "昨天", "前天", "3天前"
            - 标准日期: "2024-01-15", "2024/01/15"
            - 默认值: "今天"（节省token）
        platforms: 平台ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定时：使用 config.yaml 中配置的所有平台
                   - 支持的平台来自 config/config.yaml 的 platforms 配置
                   - 每个平台都有对应的name字段（如"知乎"、"微博"），方便AI识别
        limit: 返回条数限制，默认50，最大1000
               注意：实际返回数量可能少于请求值，取决于指定日期的新闻总数
        include_url: 是否包含URL链接，默认False（节省token）

    Returns:
        JSON格式的新闻列表，包含标题、平台、排名等信息

    **重要：数据展示建议**
    本工具会返回完整的新闻列表（通常50条）给你。但请注意：
    - **工具返回**：完整的50条数据 ✅
    - **建议展示**：向用户展示全部数据，除非用户明确要求总结
    - **用户期望**：用户可能需要完整数据，请谨慎总结

    **何时可以总结**：
    - 用户明确说"给我总结一下"或"挑重点说"
    - 数据量超过100条时，可先展示部分并询问是否查看全部

    **注意**：如果用户询问"为什么只显示了部分"，说明他们需要完整数据
    """
    tools = _get_tools()
    result = tools['data'].get_news_by_date(
        date_query=date_query,
        platforms=platforms,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)



# ==================== 高级数据分析工具 ====================

@mcp.tool
async def analyze_topic_trend(
    topic: str,
    analysis_type: str = "trend",
    date_range: Optional[Dict[str, str]] = None,
    granularity: str = "day",
    threshold: float = 3.0,
    time_window: int = 24,
    lookahead_hours: int = 6,
    confidence_threshold: float = 0.7
) -> str:
    """
    统一话题趋势分析工具 - 整合多种趋势分析模式

    Args:
        topic: 话题关键词（必需）
        analysis_type: 分析类型，可选值：
            - "trend": 热度趋势分析（追踪话题的热度变化）
            - "lifecycle": 生命周期分析（从出现到消失的完整周期）
            - "viral": 异常热度检测（识别突然爆火的话题）
            - "predict": 话题预测（预测未来可能的热点）
        date_range: 日期范围（trend和lifecycle模式），可选
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-10-18", "end": "2025-10-25"}
                    - **说明**: AI需要根据用户的自然语言（如"最近7天"）自动计算日期范围
                    - **默认**: 不指定时默认分析最近7天
        granularity: 时间粒度（trend模式），默认"day"（仅支持 day，因为底层数据按天聚合）
        threshold: 热度突增倍数阈值（viral模式），默认3.0
        time_window: 检测时间窗口小时数（viral模式），默认24
        lookahead_hours: 预测未来小时数（predict模式），默认6
        confidence_threshold: 置信度阈值（predict模式），默认0.7

    Returns:
        JSON格式的趋势分析结果

    **AI使用说明：**
    当用户使用相对时间表达时（如"最近7天"、"过去一周"、"上个月"），
    AI需要自动计算对应的日期范围并传递给 date_range 参数。

    Examples:
        - analyze_topic_trend(topic="人工智能", analysis_type="trend", date_range={"start": "2025-10-18", "end": "2025-10-25"})
        - analyze_topic_trend(topic="特斯拉", analysis_type="lifecycle", date_range={"start": "2025-10-18", "end": "2025-10-25"})
        - analyze_topic_trend(topic="比特币", analysis_type="viral", threshold=3.0)
        - analyze_topic_trend(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_topic_trend_unified(
        topic=topic,
        analysis_type=analysis_type,
        date_range=date_range,
        granularity=granularity,
        threshold=threshold,
        time_window=time_window,
        lookahead_hours=lookahead_hours,
        confidence_threshold=confidence_threshold
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_data_insights(
    insight_type: str = "platform_compare",
    topic: Optional[str] = None,
    date_range: Optional[Dict[str, str]] = None,
    min_frequency: int = 3,
    top_n: int = 20
) -> str:
    """
    统一数据洞察分析工具 - 整合多种数据分析模式

    Args:
        insight_type: 洞察类型，可选值：
            - "platform_compare": 平台对比分析（对比不同平台对话题的关注度）
            - "platform_activity": 平台活跃度统计（统计各平台发布频率和活跃时间）
            - "keyword_cooccur": 关键词共现分析（分析关键词同时出现的模式）
        topic: 话题关键词（可选，platform_compare模式适用）
        date_range: **【对象类型】** 日期范围（可选）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **重要**: 必须是对象格式，不能传递整数
        min_frequency: 最小共现频次（keyword_cooccur模式），默认3
        top_n: 返回TOP N结果（keyword_cooccur模式），默认20

    Returns:
        JSON格式的数据洞察分析结果

    Examples:
        - analyze_data_insights(insight_type="platform_compare", topic="人工智能")
        - analyze_data_insights(insight_type="platform_activity", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - analyze_data_insights(insight_type="keyword_cooccur", min_frequency=5, top_n=15)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_data_insights_unified(
        insight_type=insight_type,
        topic=topic,
        date_range=date_range,
        min_frequency=min_frequency,
        top_n=top_n
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_sentiment(
    topic: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    date_range: Optional[Dict[str, str]] = None,
    limit: int = 50,
    sort_by_weight: bool = True,
    include_url: bool = False
) -> str:
    """
    分析新闻的情感倾向和热度趋势

    Args:
        topic: 话题关键词（可选）
        platforms: 平台ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定时：使用 config.yaml 中配置的所有平台
                   - 支持的平台来自 config/config.yaml 的 platforms 配置
                   - 每个平台都有对应的name字段（如"知乎"、"微博"），方便AI识别
        date_range: **【对象类型】** 日期范围（可选）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **重要**: 必须是对象格式，不能传递整数
        limit: 返回新闻数量，默认50，最大100
               注意：本工具会对新闻标题进行去重（同一标题在不同平台只保留一次），
               因此实际返回数量可能少于请求的 limit 值
        sort_by_weight: 是否按热度权重排序，默认True
        include_url: 是否包含URL链接，默认False（节省token）

    Returns:
        JSON格式的分析结果，包含情感分布、热度趋势和相关新闻

    **重要：数据展示策略**
    - 本工具返回完整的分析结果和新闻列表
    - **默认展示方式**：展示完整的分析结果（包括所有新闻）
    - 仅在用户明确要求"总结"或"挑重点"时才进行筛选
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_sentiment(
        topic=topic,
        platforms=platforms,
        date_range=date_range,
        limit=limit,
        sort_by_weight=sort_by_weight,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def find_similar_news(
    reference_title: str,
    threshold: float = 0.6,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    查找与指定新闻标题相似的其他新闻

    Args:
        reference_title: 新闻标题（完整或部分）
        threshold: 相似度阈值，0-1之间，默认0.6
                   注意：阈值越高匹配越严格，返回结果越少
        limit: 返回条数限制，默认50，最大100
               注意：实际返回数量取决于相似度匹配结果，可能少于请求值
        include_url: 是否包含URL链接，默认False（节省token）

    Returns:
        JSON格式的相似新闻列表，包含相似度分数

    **重要：数据展示策略**
    - 本工具返回完整的相似新闻列表
    - **默认展示方式**：展示全部返回的新闻（包括相似度分数）
    - 仅在用户明确要求"总结"或"挑重点"时才进行筛选
    """
    tools = _get_tools()
    result = tools['analytics'].find_similar_news(
        reference_title=reference_title,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def generate_summary_report(
    report_type: str = "daily",
    date_range: Optional[Dict[str, str]] = None
) -> str:
    """
    每日/每周摘要生成器 - 自动生成热点摘要报告

    Args:
        report_type: 报告类型（daily/weekly）
        date_range: **【对象类型】** 自定义日期范围（可选）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **重要**: 必须是对象格式，不能传递整数

    Returns:
        JSON格式的摘要报告，包含Markdown格式内容
    """
    tools = _get_tools()
    result = tools['analytics'].generate_summary_report(
        report_type=report_type,
        date_range=date_range
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 智能检索工具 ====================

@mcp.tool
async def search_news(
    query: str,
    search_mode: str = "keyword",
    date_range: Optional[Dict[str, str]] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    sort_by: str = "relevance",
    threshold: float = 0.6,
    include_url: bool = False
) -> str:
    """
    统一搜索接口，支持多种搜索模式

    Args:
        query: 搜索关键词或内容片段
        search_mode: 搜索模式，可选值：
            - "keyword": 精确关键词匹配（默认，适合搜索特定话题）
            - "fuzzy": 模糊内容匹配（适合搜索内容片段，会过滤相似度低于阈值的结果）
            - "entity": 实体名称搜索（适合搜索人物/地点/机构）
        date_range: 日期范围（可选）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **说明**: AI需要根据用户的自然语言（如"最近7天"）自动计算日期范围
                    - **默认**: 不指定时默认查询今天的新闻
                    - **注意**: start和end可以相同（表示单日查询）
        platforms: 平台ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定时：使用 config.yaml 中配置的所有平台
                   - 支持的平台来自 config/config.yaml 的 platforms 配置
                   - 每个平台都有对应的name字段（如"知乎"、"微博"），方便AI识别
        limit: 返回条数限制，默认50，最大1000
               注意：实际返回数量取决于搜索匹配结果（特别是 fuzzy 模式下会过滤低相似度结果）
        sort_by: 排序方式，可选值：
            - "relevance": 按相关度排序（默认）
            - "weight": 按新闻权重排序
            - "date": 按日期排序
        threshold: 相似度阈值（仅fuzzy模式有效），0-1之间，默认0.6
                   注意：阈值越高匹配越严格，返回结果越少
        include_url: 是否包含URL链接，默认False（节省token）

    Returns:
        JSON格式的搜索结果，包含标题、平台、排名等信息

    **重要：数据展示策略**
    - 本工具返回完整的搜索结果列表
    - **默认展示方式**：展示全部返回的新闻，无需总结或筛选
    - 仅在用户明确要求"总结"或"挑重点"时才进行筛选

    **AI使用说明：**
    当用户使用相对时间表达时（如"最近7天"、"过去一周"、"最近半个月"），
    AI需要自动计算对应的日期范围。计算规则：
    - "最近7天" → {"start": "今天-6天", "end": "今天"}
    - "过去一周" → {"start": "今天-6天", "end": "今天"}
    - "最近30天" → {"start": "今天-29天", "end": "今天"}

    Examples:
        - 今天的新闻: search_news(query="人工智能")
        - 最近7天: search_news(query="人工智能", date_range={"start": "2025-10-18", "end": "2025-10-25"})
        - 精确日期: search_news(query="人工智能", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - 模糊搜索: search_news(query="特斯拉降价", search_mode="fuzzy", threshold=0.4)
    """
    tools = _get_tools()
    result = tools['search'].search_news_unified(
        query=query,
        search_mode=search_mode,
        date_range=date_range,
        platforms=platforms,
        limit=limit,
        sort_by=sort_by,
        threshold=threshold,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def search_related_news_history(
    reference_text: str,
    time_preset: str = "yesterday",
    threshold: float = 0.4,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    基于种子新闻，在历史数据中搜索相关新闻

    Args:
        reference_text: 参考新闻标题（完整或部分）
        time_preset: 时间范围预设值，可选：
            - "yesterday": 昨天
            - "last_week": 上周 (7天)
            - "last_month": 上个月 (30天)
            - "custom": 自定义日期范围（需要提供 start_date 和 end_date）
        threshold: 相关性阈值，0-1之间，默认0.4
                   注意：综合相似度计算（70%关键词重合 + 30%文本相似度）
                   阈值越高匹配越严格，返回结果越少
        limit: 返回条数限制，默认50，最大100
               注意：实际返回数量取决于相关性匹配结果，可能少于请求值
        include_url: 是否包含URL链接，默认False（节省token）

    Returns:
        JSON格式的相关新闻列表，包含相关性分数和时间分布

    **重要：数据展示策略**
    - 本工具返回完整的相关新闻列表
    - **默认展示方式**：展示全部返回的新闻（包括相关性分数）
    - 仅在用户明确要求"总结"或"挑重点"时才进行筛选
    """
    tools = _get_tools()
    result = tools['search'].search_related_news_history(
        reference_text=reference_text,
        time_preset=time_preset,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 配置与系统管理工具 ====================

@mcp.tool
async def get_current_config(
    section: str = "all"
) -> str:
    """
    获取当前系统配置

    Args:
        section: 配置节，可选值：
            - "all": 所有配置（默认）
            - "crawler": 爬虫配置
            - "push": 推送配置
            - "keywords": 关键词配置
            - "weights": 权重配置

    Returns:
        JSON格式的配置信息
    """
    tools = _get_tools()
    result = tools['config'].get_current_config(section=section)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_system_status() -> str:
    """
    获取系统运行状态和健康检查信息

    返回系统版本、数据统计、缓存状态等信息

    Returns:
        JSON格式的系统状态信息
    """
    tools = _get_tools()
    result = tools['system'].get_system_status()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def trigger_crawl(
    platforms: Optional[List[str]] = None,
    save_to_local: bool = False,
    include_url: bool = False
) -> str:
    """
    手动触发一次爬取任务（可选持久化）

    Args:
        platforms: 指定平台ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定时：使用 config.yaml 中配置的所有平台
                   - 支持的平台来自 config/config.yaml 的 platforms 配置
                   - 每个平台都有对应的name字段（如"知乎"、"微博"），方便AI识别
                   - 注意：失败的平台会在返回结果的 failed_platforms 字段中列出
        save_to_local: 是否保存到本地 output 目录，默认 False
        include_url: 是否包含URL链接，默认False（节省token）

    Returns:
        JSON格式的任务状态信息，包含：
        - platforms: 成功爬取的平台列表
        - failed_platforms: 失败的平台列表（如有）
        - total_news: 爬取的新闻总数
        - data: 新闻数据

    Examples:
        - 临时爬取: trigger_crawl(platforms=['zhihu'])
        - 爬取并保存: trigger_crawl(platforms=['weibo'], save_to_local=True)
        - 使用默认平台: trigger_crawl()  # 爬取config.yaml中配置的所有平台
    """
    tools = _get_tools()
    result = tools['system'].trigger_crawl(platforms=platforms, save_to_local=save_to_local, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 启动入口 ====================

def run_server(
    project_root: Optional[str] = None,
    transport: str = 'stdio',
    host: str = '0.0.0.0',
    port: int = 3333
):
    """
    启动 MCP 服务器

    Args:
        project_root: 项目根目录路径
        transport: 传输模式，'stdio' 或 'http'
        host: HTTP模式的监听地址，默认 0.0.0.0
        port: HTTP模式的监听端口，默认 3333
    """
    # 初始化工具实例
    _get_tools(project_root)

    # 打印启动信息
    print()
    print("=" * 60)
    print("  TrendRadar MCP Server - FastMCP 2.0")
    print("=" * 60)
    print(f"  传输模式: {transport.upper()}")

    if transport == 'stdio':
        print("  协议: MCP over stdio (标准输入输出)")
        print("  说明: 通过标准输入输出与 MCP 客户端通信")
    elif transport == 'http':
        print(f"  监听地址: http://{host}:{port}")
        print(f"  HTTP端点: http://{host}:{port}/mcp")
        print("  协议: MCP over HTTP (生产环境)")
        if SERVER_PASSWORD:
            print(f"  🔐 认证状态: ✅ 启用")
            print(f"  🔑 访问密码: 已设置 (长度: {len(SERVER_PASSWORD)} 字符)")
            print(f"  📝 访问方式:")
            print(f"     1. URL参数: http://{host}:{port}/mcp?pwd=<your_password>")
            print(f"     2. 请求头: curl -H 'X-MCP-Password: <your_password>' http://{host}:{port}/mcp")
        else:
            print(f"  🔓 认证状态: ❌ 关闭 (未设置MCP_SERVER_PASSWORD环境变量)")

    if project_root:
        print(f"  项目目录: {project_root}")
    else:
        print("  项目目录: 当前目录")

    print()
    print("  已注册的工具:")
    print("    === 基础数据查询（P0核心）===")
    print("    1. get_latest_news        - 获取最新新闻")
    print("    2. get_news_by_date       - 按日期查询新闻（支持自然语言）")
    print("    3. get_trending_topics    - 获取趋势话题")
    print()
    print("    === 智能检索工具 ===")
    print("    4. search_news                  - 统一新闻搜索（关键词/模糊/实体）")
    print("    5. search_related_news_history  - 历史相关新闻检索")
    print()
    print("    === 高级数据分析 ===")
    print("    6. analyze_topic_trend      - 统一话题趋势分析（热度/生命周期/爆火/预测）")
    print("    7. analyze_data_insights    - 统一数据洞察分析（平台对比/活跃度/关键词共现）")
    print("    8. analyze_sentiment        - 情感倾向分析")
    print("    9. find_similar_news        - 相似新闻查找")
    print("    10. generate_summary_report - 每日/每周摘要生成")
    print()
    print("    === 配置与系统管理 ===")
    print("    11. get_current_config      - 获取当前系统配置")
    print("    12. get_system_status       - 获取系统运行状态")
    print("    13. trigger_crawl           - 手动触发爬取任务")
    print("=" * 60)
    print()

    # 根据传输模式运行服务器
    if transport == 'stdio':
        mcp.run(transport='stdio')
    elif transport == 'http':
        # HTTP 模式（生产推荐）
        mcp.run(
            transport='http',
            host=host,
            port=port,
            path='/mcp'  # HTTP 端点路径
        )
    else:
        raise ValueError(f"不支持的传输模式: {transport}")


if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='TrendRadar MCP Server - 新闻热点聚合 MCP 工具服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # STDIO 模式（用于 Cherry Studio）
  uv run python mcp_server/server.py

  # HTTP 模式（适合远程访问）
  uv run python mcp_server/server.py --transport http --port 3333

Cherry Studio 配置示例:
  设置 > MCP Servers > 添加服务器
  - 名称: TrendRadar
  - 类型: STDIO
  - 命令: [UV的完整路径]
  - 参数: --directory [项目路径] run python mcp_server/server.py

详细配置教程请查看: README-Cherry-Studio.md
        """
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http'],
        default='stdio',
        help='传输模式：stdio (默认) 或 http (生产环境)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='HTTP模式的监听地址，默认 0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3333,
        help='HTTP模式的监听端口，默认 3333'
    )
    parser.add_argument(
        '--project-root',
        help='项目根目录路径'
    )

    args = parser.parse_args()

    run_server(
        project_root=args.project_root,
        transport=args.transport,
        host=args.host,
        port=args.port
    )
