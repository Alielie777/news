import json
from typing import Any

import redis.asyncio as redis


REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# 创建redis的连接对象
redis_client = redis.Redis(
    host=REDIS_HOST,      # redis服务器主机地址
    port=REDIS_PORT,      # redis端口号
    db=REDIS_DB  ,        # redis数据库编号 0～15
    decode_responses=True # 是否将字节数据解码为字符数据
)

# 读取缓存：字符串
async def get_cache(key:str):
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败：{e}")
        return None

# 读取缓存：列表或字典
async def get_json_cache(key:str):
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data) # 反序列化
        return None
    except Exception as e:
        print(f"获取 JSON 缓存失败：{e}")
        return None

# 设置缓存: key 键，value 值，expire 过期时间
async def set_cache(key:str, value:Any, expire:int=3600):
    try:
        # 判断value类型是否为字典或者列表
        if isinstance(value,(dict,list)):
            # 转字符串再设置为缓存 ensure_ascii=False: 中文正常保存
            value = json.dumps(value, ensure_ascii=False)
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        print(f"设置缓存失败：{e}")
        return False
