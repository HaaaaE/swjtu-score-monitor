import os
from scraper.fetcher import ScoreFetcher

username = os.environ.get("SWJTU_USERNAME")
password = os.environ.get("SWJTU_PASSWORD")

# if not username or not password:
#     raise HTTPException(status_code=500, detail="服务器未配置学号或密码环境变量")

print("--- 任务开始: 准备获取成绩 ---")
fetcher = ScoreFetcher(username=username, password=password)

# 1. 登录
login_success = fetcher.login()
# if not login_success:
#     return {"status": "error", "message": "登录失败，请检查Vercel日志。"}

# 2. 获取并合并总成绩和平时成绩
ns = fetcher.get_normal_scores()
es = fetcher.get_all_scores()
print(ns, es)
# if not combined_scores:
#     return {"status": "error", "message": "未能获取到任何成绩数据。"}

# 3. 将合并后的成绩数据存入PostgreSQL数据库

