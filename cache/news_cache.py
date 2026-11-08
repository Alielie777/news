"""
新闻相关的缓存方法
"""
from typing import List, Dict, Any, Optional
from config.cache_config import get_json_cache,set_cache

# key-value
CATEGORY_KEY = "news:categories"
NEWS_LIST_KEY_PREFIX = "news:list"

# 获取新闻分类缓存
async def get_cached_categories():
    return await get_json_cache(CATEGORY_KEY)

# 写入新闻分类缓存
# 分类、配置：7200 列表：600 详情：1800 --数据越稳定，缓存越持久
async def set_cached_categories(data: List[Dict[str, Any]],expire: int = 7200):
    return await set_cache(CATEGORY_KEY, data, expire)

# 读取新闻列表缓存
async def get_cached_news_list(category_id: Optional[int], page:int, page_size:int):
    # 处理key
    category_part = category_id if category_id is not None else "all"
    key = f"{NEWS_LIST_KEY_PREFIX}:{category_part}:{page}:{page_size}"
    return await get_json_cache(key)


# 写入新闻列表缓存 key = news_list:分类id:页码:每页数量 + 列表数据 + 过期时间
async def set_cached_news_list(category_id: Optional[int], page:int, page_size:int, news_list:List[Dict[str, Any]],expire: int = 1800):
    # 处理key
    category_part = category_id if category_id is not None else "all"
    key = f"{NEWS_LIST_KEY_PREFIX}:{category_part}:{page}:{page_size}"
    # 调用封装的 Redis 设置方法，存新闻列表到缓存
    return await set_cache(key, news_list, expire)
