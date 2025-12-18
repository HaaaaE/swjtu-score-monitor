import json
import os
import requests
from datetime import datetime, timezone

# --- 配置部分 ---
GIST_PAT = os.getenv("GIST_PAT")
# 默认文件名为 scores.json，用户也可以通过环境变量覆盖
GIST_FILENAME = os.getenv("GIST_NAME", "scores.json")
# 双重保险
TARGET_DESCRIPTION = "just_for_swjtu_scores_monotor"

if not GIST_PAT:
    raise ValueError("严重错误: 必须设置 GIST_PAT 环境变量")

# 确保文件名以 .json 结尾
if not GIST_FILENAME.endswith(".json"):
    GIST_FILENAME += ".json"

_CACHED_GIST_ID = None

BASE_URL = "https://api.github.com/gists"
HEADERS = {
    "Authorization": f"token {GIST_PAT}",
    "Accept": "application/vnd.github.v3+json"
}

def _get_or_create_gist_id():
    """
    双重验证查找逻辑：
    1. 描述必须完全匹配 TARGET_DESCRIPTION
    2. 文件列表中必须包含 GIST_FILENAME
    """
    global _CACHED_GIST_ID
    if _CACHED_GIST_ID:
        return _CACHED_GIST_ID

    print(f"--- 正在根据双重特征查找 Gist... ---")
    print(f"   1. 描述: {TARGET_DESCRIPTION}")
    print(f"   2. 文件: {GIST_FILENAME}")

    try:
        # 获取用户的所有 Gist
        response = requests.get(BASE_URL, headers=HEADERS)
        response.raise_for_status()
        gists = response.json()

        for gist in gists:
            
            # 校验 1: 检查描述 (处理 description 为 None 的情况)
            current_desc = gist.get("description") or ""
            if current_desc != TARGET_DESCRIPTION:
                continue  # 描述不对，直接跳过
            
            # 校验 2: 检查文件名
            files = gist.get("files", {})
            if GIST_FILENAME in files:
                # 只有两个条件都满足，才认为是我们要找的那个
                _CACHED_GIST_ID = gist["id"]
                print(f"--- 成功匹配到 Gist ID: {_CACHED_GIST_ID} ---")
                return _CACHED_GIST_ID
            
        # 如果没找到，创建新的
        print(f"--- 未找到匹配的双重特征 Gist，正在创建新的... ---")
        
        create_payload = {
            "description": TARGET_DESCRIPTION,  # 写入特定的描述暗号
            "public": False,
            "files": {
                GIST_FILENAME: {
                    "content": "[]"
                }
            }
        }
        
        create_response = requests.post(BASE_URL, headers=HEADERS, json=create_payload)
        create_response.raise_for_status()
        
        new_gist = create_response.json()
        _CACHED_GIST_ID = new_gist["id"]
        print(f"--- 创建成功，新 Gist ID: {_CACHED_GIST_ID} ---")
        return _CACHED_GIST_ID

    except requests.exceptions.RequestException as e:
        print(f"GitHub API 操作失败: {e}")
        raise e

# 下面的 save_scores 和 get_latest_scores 函数逻辑不变，
# 它们会自动调用上面更新过的 _get_or_create_gist_id
def save_scores(scores: list, ttl_seconds: int = None):
    try:
        gist_id = _get_or_create_gist_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        content_str = json.dumps(scores, ensure_ascii=False, indent=2)
        
        update_url = f"{BASE_URL}/{gist_id}"
        payload = {
            "files": {
                GIST_FILENAME: {
                    "content": content_str
                }
            }
        }
        
        response = requests.patch(update_url, headers=HEADERS, json=payload)
        response.raise_for_status()
        
        print(f"--- 成功保存到 Gist ({GIST_FILENAME}) ---")
        return f"{gist_id}@{timestamp}"
    except Exception as e:
        print(f"保存失败: {e}")
        return None

def get_latest_scores():
    try:
        gist_id = _get_or_create_gist_id()
        get_url = f"{BASE_URL}/{gist_id}"
        
        response = requests.get(get_url, headers=HEADERS)
        response.raise_for_status()
        
        data = response.json()
        files = data.get("files", {})
        
        if GIST_FILENAME not in files:
            return []
            
        file_content = files[GIST_FILENAME].get("content")
        return json.loads(file_content) if file_content else []

    except Exception as e:
        print(f"读取失败: {e}")
        return None