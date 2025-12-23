# scraper/fetcher.py
import requests
from bs4 import BeautifulSoup
import time
import logging

from pathlib import Path
import sys, os
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import ocr  # 导入自定义OCR模块
from urllib.parse import urlparse

# --- 配置与常量 ---
BASE_URL = "https://jwc.swjtu.edu.cn"

# 发起请求，允许重定向
response = requests.get(
    BASE_URL,
    timeout=5,
    allow_redirects=True,  # 自动跟随重定向
    verify=True  # 验证 SSL 证书
)

# 解析最终的 URL
final_url = response.url
parsed = urlparse(final_url)
final_protocol = parsed.scheme
if final_protocol == "http":
    BASE_URL = "http://jwc.swjtu.edu.cn"
    print("检测到教务使用 HTTP，已切换为 HTTP 访问。")

LOGIN_PAGE_URL = f"{BASE_URL}/service/login.html"
LOGIN_API_URL = f"{BASE_URL}/vatuu/UserLoginAction"
CAPTCHA_URL = f"{BASE_URL}/vatuu/GetRandomNumberToJPEG"
LOADING_URL = f"{BASE_URL}/vatuu/UserLoadingAction"
ALL_SCORES_URL = f"{BASE_URL}/vatuu/StudentScoreInfoAction?setAction=studentScoreQuery&viewType=studentScore&orderType=submitDate&orderValue=desc"
NORMAL_SCORES_URL = f"{BASE_URL}/vatuu/StudentScoreInfoAction?setAction=studentNormalMark"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Origin': BASE_URL,
}

class ScoreFetcher:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.is_logged_in = False

    def login(self, max_retries=10, retry_delay=1):
        for attempt in range(1, max_retries + 1):
            print(f"--- 登录尝试 #{attempt}/{max_retries} ---")
            
            try:
                # 1. 获取并识别验证码
                print("正在获取验证码...")
                captcha_params = {'test': int(time.time() * 1000)}
                response = self.session.get(CAPTCHA_URL, params=captcha_params, timeout=10)
                response.raise_for_status()
                captcha_code = ocr.classify(response.content)
                print(f"OCR 识别结果: {captcha_code}")
                if not captcha_code or len(captcha_code) != 4:
                    print("验证码识别失败，跳过本次尝试。")
                    if attempt < max_retries: time.sleep(retry_delay)
                    continue

                # 2. 尝试API登录
                print("正在尝试登录API...")
                login_payload = { 'username': self.username, 'password': self.password, 'ranstring': captcha_code, 'url': '', 'returnType': '', 'returnUrl': '', 'area': '' }
                response = self.session.post(LOGIN_API_URL, data=login_payload, headers={'Referer': LOGIN_PAGE_URL}, timeout=10)
                response.raise_for_status()
                login_result = response.json()

                if login_result.get('loginStatus') == '1':
                    print(f"API验证成功！{login_result.get('loginMsg')[0:5]}")
                    print("正在访问加载页面以建立完整会话...")
                    self.session.get(LOADING_URL, headers={'Referer': LOGIN_PAGE_URL}, timeout=10)
                    print("会话建立成功，已登录。")
                    self.is_logged_in = True
                    return True
                else:
                    print(f"登录API失败: {login_result.get('loginMsg', '未知错误')}")
            
            except Exception as e:
                print(f"登录过程中发生异常: {e}")

            if attempt < max_retries:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
        
        print(f"\n登录失败 {max_retries} 次，程序终止。")
        return False

    def get_all_scores(self):
        if not self.is_logged_in:
            print("错误：未登录。")
            return None

        print("\n正在查询全部成绩记录...")
        try:
            response = self.session.get(ALL_SCORES_URL, headers={'Referer': LOADING_URL}, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            score_table = soup.find('table', id='table3')
            if not score_table:
                print("错误：未找到全部成绩表格。")
                return None

            all_rows_data = []
            header = [th.text.strip() for th in score_table.find('tr').find_all('th')]
            
            for row in score_table.find_all('tr')[1:]:
                cols = [ele.text.strip() for ele in row.find_all('td')]
                if len(cols) == len(header):
                    all_rows_data.append(dict(zip(header, cols)))
            
            print(f"成功获取到 {len(all_rows_data)} 条总成绩记录。")
            return all_rows_data

        except Exception as e:
            print(f"获取全部成绩时出错: {e}")
            return None

    def get_normal_scores(self):
        if not self.is_logged_in:
            print("错误：未登录。")
            return None

        print("\n正在查询平时成绩明细...")
        try:
            response = self.session.get(NORMAL_SCORES_URL, headers={'Referer': ALL_SCORES_URL}, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            score_table = soup.find('table', id='table3')
            if not score_table:
                print("错误：未找到平时成绩表格。")
                return None
            
            normal_scores_data = []
            current_course_info = {}
            for row in score_table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) == 11:
                    course_name = cols[3].text.strip()
                    if not current_course_info or current_course_info.get("课程名称") != course_name:
                        if current_course_info:
                            normal_scores_data.append(current_course_info)
                        current_course_info = {
                            "课程名称": course_name,
                            "教师": cols[5].text.strip(),
                            "详情": []
                        }
                    
                    current_course_info["详情"].append({
                        "平时成绩名称": cols[6].text.strip(),
                        "成绩": cols[8].text.strip(),
                        "占比": cols[7].text.strip(),
                        "提交时间": cols[10].text.strip()
                    })
                
                elif len(cols) == 1 and cols[0].get('colspan') == '11':
                    if current_course_info:
                        current_course_info["总结"] = cols[0].text.strip()
            
            if current_course_info: # 添加最后一个课程
                normal_scores_data.append(current_course_info)

            print(f"成功获取到 {len(normal_scores_data)} 门课程的平时成绩明细。")
            return normal_scores_data

        except Exception as e:
            print(f"获取平时成绩时出错: {e}")
            return None

    def get_combined_scores(self):
        """
        获取总成绩和平时成绩，并将它们合并。
        """
        if not self.is_logged_in:
            print("错误：未登录。")
            return None

        all_scores = self.get_all_scores()
        time.sleep(1) # 模拟人类行为
        normal_scores = self.get_normal_scores()

        if not all_scores:
            print("未能获取总成绩，无法进行合并。")
            raise Exception("未能获取总成绩，无法进行合并。")

        if not normal_scores:
            print("未能获取平时成绩。")
            raise Exception("未能获取平时成绩。")

        # 创建一个快速查找平时成绩的字典
        # key: (课程名称, 教师)
        normal_scores_map = {(ns['课程名称'], ns['教师']): {
            '详情': ns['详情'],
            '总结': ns.get('总结')  # 包含summary信息
        } for ns in normal_scores}
        
        # 遍历总成绩，将平时成绩详情合并进去
        for score_record in all_scores:
            key = (score_record['课程名称'], score_record['教师'])
            if key in normal_scores_map:
                normal_data = normal_scores_map[key]
                score_record['平时成绩详情'] = normal_data['详情']
                score_record['平时成绩总结'] = normal_data['总结']
            else:
                score_record['平时成绩详情'] = None
                score_record['平时成绩总结'] = None

        print("总成绩与平时成绩合并完成。")
        return all_scores
   
import requests
from urllib.parse import urlparse

def detect_base_url(domain, test_path='/', timeout=5):
    """
    自动检测网站实际使用的协议（HTTP/HTTPS）
    通过尝试访问并跟随重定向来判断
    
    Args:
        domain: 域名，如 'jwc.swjtu.edu.cn'
        test_path: 测试路径，默认为根路径
        timeout: 超时时间（秒）
    
    Returns:
        str: 实际使用的 BASE_URL，如 'http://jwc.swjtu.edu.cn'
    """
    print(f"🔍 正在检测 {domain} 的访问协议...")
    
    # 优先尝试 HTTPS（现代标准）
    for protocol in ['https', 'http']:
        test_url = f"{protocol}://{domain}{test_path}"
        
        try:
            print(f"  📡 尝试 {protocol.upper()} ...")
            
            # 发起请求，允许重定向
            response = requests.get(
                test_url,
                timeout=timeout,
                allow_redirects=True,  # 自动跟随重定向
                verify=True  # 验证 SSL 证书
            )
            
            # 解析最终的 URL
            final_url = response.url
            parsed = urlparse(final_url)
            final_protocol = parsed.scheme
            final_domain = parsed.netloc
            
            # 检查是否发生了重定向
            if response.history:
                print(f"  ↪️  发生了 {len(response.history)} 次重定向:")
                for i, resp in enumerate(response.history, 1):
                    print(f"      {i}. {resp.url} → {resp.status_code} {resp.reason}")
            
            print(f"  ✅ 最终访问: {final_url}")
            print(f"  🔐 使用协议: {final_protocol.upper()}")
            print(f"  📊 状态码: {response.status_code}")
            
            # 检测到协议降级
            if protocol == 'https' and final_protocol == 'http':
                print(f"  ⚠️  服务器将 HTTPS 重定向到 HTTP")
                print(f"  💡 建议直接使用 HTTP 协议以避免 Cookie 问题")
            
            # 构造 BASE_URL
            base_url = f"{final_protocol}://{final_domain}"
            
            print(f"\n✨ 检测完成！使用: {base_url}\n")
            return base_url
            
        except requests.exceptions.SSLError as e:
            print(f"  ❌ SSL 证书错误")
            print(f"  💡 {protocol.upper()} 不可用，继续尝试...")
            continue
            
        except requests.exceptions.ConnectionError as e:
            print(f"  ❌ 连接失败")
            print(f"  💡 {protocol.upper()} 无法访问，继续尝试...")
            continue
            
        except requests.exceptions.Timeout:
            print(f"  ❌ 连接超时（>{timeout}秒）")
            continue
            
        except Exception as e:
            print(f"  ❌ 未知错误: {type(e).__name__}: {e}")
            continue
    
    # 所有协议都失败，默认使用 HTTP
    print(f"⚠️  无法自动检测，默认使用: http://{domain}\n")
    return f"http://{domain}"

if __name__ == "__main__":
    print(detect_base_url("jwc.swjtu.edu.cn"))