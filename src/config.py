import json
import os

def load_config():
    """加载配置文件"""
    if not os.path.exists("config.json"):
        raise FileNotFoundError("配置文件 config.json 不存在，请先创建配置文件")
    
    with open("config.json", "r", encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """保存配置文件"""
    with open("config.json", "w", encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False) 