# --- query_scores.py (最终版，输出所有表格信息) ---
import requests
from bs4 import BeautifulSoup
import time
import getpass
import config  # 从配置文件导入账号密码
import ddddocr

# --- 配置与常量 ---
BASE_URL = "https://jwc.swjtu.edu.cn"
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
    """
    一个专注于获取西南交通大学教务系统成绩的客户端。
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.is_logged_in = False
        self.ocr = ddddocr.DdddOcr(show_ad=False)

# --- 在 ScoreFetcher 类中 ---
# 用这个新函数完整替换旧的 login 函数

    def login(self,max_retries,retry_delay):
        """
        完整的登录流程，包括获取验证码、OCR识别、API登录、会话建立，
        并在失败时进行延时重试。
        """

        for attempt in range(1, max_retries + 1):
            print(f"--- 登录尝试 #{attempt}/{max_retries} ---")
            
            # 1. 获取验证码并尝试OCR识别
            print("正在获取验证碼...")
            captcha_code = None
            try:
                captcha_params = {'test': int(time.time() * 1000)}
                response = self.session.get(CAPTCHA_URL, params=captcha_params)
                response.raise_for_status()
                image_bytes = response.content
                
                # 使用ddddocr识别
                self.ocr.set_ranges(2)
                captcha_code = self.ocr.classification(image_bytes)
                print(f"ddddocr 识别结果: {captcha_code}")
                
            except Exception as e:
                print(f"获取或识别验证码失败: {e}")
                # 即使验证码失败，也尝试继续登录，因为有时可能是临时问题
                # 但为了保险，如果识别结果是None，我们还是退出
                if captcha_code is None:
                    print("无法获取或识别验证码，本次重试失败。")
                    if attempt < max_retries:
                        print(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                    continue # 继续下一次尝试
            
            # 2. 尝试API登录
            print("正在尝试登录API...")
            login_payload = { 'username': self.username, 'password': self.password, 'ranstring': captcha_code, 'url': '', 'returnType': '', 'returnUrl': '', 'area': '' }
            login_headers = self.session.headers.copy()
            login_headers['Referer'] = LOGIN_PAGE_URL
            try:
                response = self.session.post(LOGIN_API_URL, data=login_payload, headers=login_headers)
                response.raise_for_status()
                login_result = response.json()
                if not login_result.get('loginStatus') == '1':
                    print(f"登录API失败: {login_result.get('loginMsg', '服务器未返回明确错误信息')} (可能是验证码错误或密码错误)")
                    # 即使API登录失败，也可能因为验证码错误，所以要看后面的会话建立是否成功
                else:
                    print(f"API验证成功！{login_result.get('loginMsg')}")
                    # 如果API验证成功，我们尝试建立会话
                    print("正在访问加载页面以建立完整会话...")
                    loading_headers = self.session.headers.copy()
                    loading_headers['Referer'] = LOGIN_PAGE_URL
                    response_loading = self.session.get(LOADING_URL, headers=loading_headers)
                    response_loading.raise_for_status()
                    print("会话建立成功，已登录。")
                    self.is_logged_in = True
                    return True # 成功登录，退出循环
                    
            except Exception as e:
                print(f"登录请求异常: {e}")
                # 任何异常都算作登录失败

            # 如果执行到这里，说明本次尝试未成功登录
            if self.is_logged_in: # 理论上前面成功了会return，这里是备用
                return True
            
            print("登录失败。")
            if attempt < max_retries:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
        
        # 如果循环结束还没有成功登录
        print(f"\n登录失败 {max_retries} 次，程序终止。请检查账号、密码、验证码或网络连接。")
        return False
    
    def get_all_scores(self):
        """获取并解析全部成绩记录（输出所有列）"""
        if not self.is_logged_in:
            print("错误：未登录，无法查询成绩。")
            return

        print("\n" + "="*80)
        print("||" + "                   1. 查询全部成绩记录 (完整信息)".ljust(78) + "||")
        print("="*80)
        try:
            headers = self.session.headers.copy()
            headers['Referer'] = LOADING_URL
            response = self.session.get(ALL_SCORES_URL, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            score_table = soup.find('table', id='table3')
            if not score_table:
                print("错误：未找到成绩表格。")
                return

            all_rows_data = []
            header = [th.text.strip() for th in score_table.find('tr').find_all('th')]
            
            for row in score_table.find_all('tr')[1:]:
                cols = [ele.text.strip() for ele in row.find_all('td')]
                if len(cols) == len(header):
                    all_rows_data.append(dict(zip(header, cols)))
            
            print(f"成功获取到 {len(all_rows_data)} 条总成绩记录。\n")
            for record in all_rows_data:
                print(f"【{record['课程名称']}】")
                print(f"  - 学年学期: {record['学年']}-{record['学期']} | 成绩: {record['成绩']} | 学分: {record['学分']} | 课程性质: {record['性质']}")
                print(f"  - 课程代码: {record['代码']} | 班号: {record['班号']} | 教师: {record['教师']}")
                print(f"  - 成绩构成: 期末({record['期末']}), 平时({record['平时']})")
                print(f"  - 考试类型: {record['类型']} | 分制: {record.get('分制', 'N/A')} | 备注: {record['备注']}\n")

        except Exception as e:
            print(f"获取全部成绩时出错: {e}")

    def get_normal_scores(self):
        """获取并解析平时成绩（输出所有列）"""
        if not self.is_logged_in:
            print("错误：未登录，无法查询成绩。")
            return

        print("\n" + "="*80)
        print("||" + "                   2. 查询平时成绩明细 (完整信息)".ljust(78) + "||")
        print("="*80)
        try:
            headers = self.session.headers.copy()
            headers['Referer'] = ALL_SCORES_URL
            response = self.session.get(NORMAL_SCORES_URL, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            score_table = soup.find('table', id='table3')
            if not score_table:
                print("错误：未找到平时成绩表格。")
                return
            
            current_course = ""
            for row in score_table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) == 11:
                    course_name = cols[3].text.strip()
                    if course_name != current_course:
                        current_course = course_name
                        print(f"\n课程: 《{current_course}》 (教师: {cols[5].text.strip()})")
                    
                    print(f"  - 项目: {cols[6].text.strip():<15} | 成绩: {cols[8].text.strip():<6} | 占比: {cols[7].text.strip():<7} | 提交时间: {cols[10].text.strip()}")
                
                elif len(cols) == 1 and cols[0].get('colspan') == '11':
                    summary_text = cols[0].text.strip()
                    print(f"  -> {summary_text}")

        except Exception as e:
            print(f"获取平时成绩时出错: {e}")


if __name__ == "__main__":
    print("--- 西南交大教务处成绩查询脚本 ---")
    
    username = config.USERNAME
    password = config.PASSWORD

    if not password:
        password = getpass.getpass(f"请输入学号 '{username}' 的密码: ")

    if not username or not password:
        print("错误：学号或密码不能为空！")
    else:
        fetcher = ScoreFetcher(username=username, password=password)
        
        if fetcher.login(max_retries=10, retry_delay=10):
            fetcher.get_all_scores()
            time.sleep(2)
            fetcher.get_normal_scores()
            print("\n所有查询任务已完成。")