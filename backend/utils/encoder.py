# utils/encoder.py
import json
from datetime import datetime


class TelegramJSONEncoder(json.JSONEncoder):
    """
    自定义 JSON 序列化器，用于处理 Telegram 特有的日期和字节对象
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.hex()  # 字节数据转为十六进制字符串
        return super().default(obj)
