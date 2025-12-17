# api/index.py
import os
from fastapi import FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyQuery
from fastapi.responses import PlainTextResponse
from pathlib import Path
import sys, os
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.fetcher import ScoreFetcher
from scraper import database

app = FastAPI()

api_key_query = APIKeyQuery(name="secret", auto_error=False)

def get_api_key(api_key: str = Security(api_key_query)):
    expected_api_key = os.environ.get("API_SECRET_TOKEN")
    if not expected_api_key:
        raise HTTPException(status_code=500, detail="服务器未配置API密钥")
    if api_key == expected_api_key:
        return api_key
    else:
        raise HTTPException(status_code=403, detail="提供的密钥无效或缺失")

@app.get("/api/fetch-scores") 
@app.post("/api/fetch-scores")
async def trigger_fetch_scores(api_key: str = Security(get_api_key)):
    username = os.environ.get("SWJTU_USERNAME")
    password = os.environ.get("SWJTU_PASSWORD")

    if not username or not password:
        raise HTTPException(status_code=500, detail="服务器未配置学号或密码环境变量")

    print("--- 任务开始: 准备获取成绩 ---")
    fetcher = ScoreFetcher(username=username, password=password)

    try:
        # 1. 登录
        login_success = fetcher.login()
        if not login_success:
            return {"status": "error", "message": "登录失败，请检查Vercel日志。"}

        # 2. 获取并合并总成绩和平时成绩
        combined_scores = fetcher.get_combined_scores()

        if not combined_scores:
            return {"status": "error", "message": "未能获取到任何成绩数据。"}

        # 3. 将合并后的成绩数据存入
        print("正在将成绩数据存入数据库...")
        old = database.get_latest_scores()
        upsert_results = database.save_scores(combined_scores)
        new = database.get_latest_scores()
        print("--- 任务完成 ---")
        return {
            "status": "success",
            "message": "成绩获取和存储任务已完成。",
            "summary": {
                "total_records_processed": len(combined_scores),
                "old_records": old,
                "fetched_records": combined_scores,
                "new_records_key": upsert_results,
                "existing_records": new,
            }
        }

    except Exception as e:
        print(f"执行任务时发生严重错误: {e}")
        raise HTTPException(status_code=500, detail=f"执行爬虫任务时发生内部错误: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "online", "message": "SWJTU Score Fetcher API is running with upstash."}

if __name__ == "__main__":
    sf = ScoreFetcher("2023112590", os.environ.get("SWJTU_PASSWORD"))  # 仅用于本地测试
    sf.login()
    sc = sf.get_combined_scores()  # 仅用于本地测试
    print(sc)