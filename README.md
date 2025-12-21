# 西南交大成绩监控系统

自动监控西南交通大学教务系统的成绩变化，当检测到新成绩或成绩更新时，通过邮件发送通知。使用 QQ 邮箱可以做到直接收到微信通知。

**功能特点：**
- 🆓 完全免费，利用 GitHub Action
- ☁️ **无需克隆代码配置环境，也无需自己的服务器**
- ⏰ 自动定时运行（北京时间 6:00-23:59，每20分钟检查一次）
- 🔒 隐私安全，敏感信息加密存储
- 📧 成绩变化时自动邮件通知

## 一、隐私与安全说明

### 为什么本项目是安全的？

1. **所有敏感信息都存储在 GitHub Secrets 中**
   - 学号、密码、邮箱授权码等信息不会出现在代码中
   - GitHub Secrets 使用加密存储，外部无法访问
   - 运行日志中 Secrets 会被自动隐藏（显示为 `***`）
   - 运行结果仅你本人可见

2. **仓库可公开**
   - Fork 后的仓库可以是公开的，不影响安全性
   - 代码中不包含任何密码或敏感信息
   - 只有你能在自己的仓库中配置 Secrets

3. **数据存储方式**
   - 成绩数据存储在你自己的 GitHub Gist 中（私有）
   - 只有你的 Personal Access Token 能访问
   - **Gist 可见性说明**：
     - 程序创建的 Gist 默认为 **Secret（私密）** 类型
     - Secret Gist 不会出现在你的公开 Gist 列表中
     - 只有知道 Gist URL 或拥有 Token 的人才能访问
     - 即使仓库是公开的，Gist 数据也是私密的

### ⚠️ 安全使用原则

- 永远不要把密码直接写在代码文件中
- 永远使用 GitHub Secrets 来存储敏感信息
- 不要将 Secrets 的值分享给他人
- **邮箱授权码和 Token 仅显示一次，请妥善保存**


## 二、前置准备

### 2.1 你需要准备

1. **你的 GitHub 账号**
2. **西南交大教务系统账号密码**
3. **一个邮箱**（推荐使用QQ邮箱，可以绑定微信收取实时通知）

### 3.2 获取每个 Secret（密钥配置）

#### ① SWJTU_USERNAME 和 SWJTU_PASSWORD

- `SWJTU_USERNAME`：你的教务系统**学号**
- `SWJTU_PASSWORD`：你的教务系统**密码**

#### ② SMTP_HOST、NOTIFY_EMAIL 和 EMAIL_PASSWORD

这三个配置用于发送邮件通知，推荐使用 QQ 邮箱

本项目采用「**自己给自己发邮件**」的设计：

- `NOTIFY_EMAIL` 既是发件人，也是收件人
- 你只需要配置一个邮箱地址
- 程序用你的邮箱给你自己发送通知

**设计原因**
1. **配置简单**：只需一个邮箱，无需额外准备发件邮箱
2. **安全可靠**：邮件在你自己的邮箱之间传递

**推荐使用 QQ 邮箱的原因：**
- QQ 邮箱可以绑定微信，收到邮件时微信会立即推送通知
- 相当于免费获得了微信消息提醒功能
- 设置方法：微信搜索「QQ邮箱提醒」进入 QQ 邮箱提醒功能，绑定该 QQ 邮箱，设置选择接受邮件提醒即可

以下是QQ邮箱的配置方法：

1. **SMTP_HOST**：`smtp.qq.com`
2. **NOTIFY_EMAIL**：你的 QQ 邮箱地址（如 `12345678@qq.com`）
3. **EMAIL_PASSWORD**：需要获取**授权码**（不是QQ密码）

**如何获取 QQ 邮箱授权码：**

1. 登录 QQ 邮箱网页版：https://mail.qq.com
2. 进入「账号与安全」
3. 进入「安全设置」
4. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」并开启
5. 点击「生成授权码」
6. 获得一个 16 位授权码（如：`abcdabcdabcdabcd`）
7. 这个授权码就是 EMAIL_PASSWORD 的值，**该字符串仅在授权码页面展示一次，请合理保存**
8. 途中可能经过三次手机号验证，这是正常的

#### ③ GIST_PAT（GitHub Personal Access Token）

GitHub Personal Access Token（个人访问令牌）是用来授权程序访问你的 GitHub Gist 的凭证。本项目使用 Gist 来存储你的成绩数据。

**如何创建 GIST_PAT：**

1. **登录 GitHub**，点击右上角头像

2. **进入 Settings**
   - 点击下拉菜单中的「Settings」

3. **找到 Developer settings**
   - 在左侧菜单最底部点击「Developer settings」

4. **创建 Personal access tokens**
   - 点击左侧「Personal access tokens」→「Tokens (classic)」
   - 点击右上角「Generate new token」→「Generate new token (classic)」

5. **配置 Token**
   - **Note**（备注）：填写一个描述，如 `swjtu-scores-monitor`
   - **Expiration**（有效期）：建议选择「No expiration」（永不过期）或「1 year」
   - **Select scopes**（权限选择）：**只勾选 `gist`**
     ```
     ☑️ gist
         Create gists
     ```
   - 其他权限不勾选

6. **生成并保存**
   - 点击底部「Generate token」
   - 复制生成的 Token（格式如：`ghp_xxxxxxxxxxxxxxxxxxxx`）
   - **重要：这个 Token 也只会显示一次，请立即复制保存**
   - 这个 Token 就是 `GIST_PAT` 的值


## 三、部署步骤

### 步骤 1：Fork 本项目

1. 在项目主页点击右上角「Fork」按钮
2. Fork 到你自己的账号下

### 步骤 2：配置 GitHub Secrets

1. 进入你 Fork 的仓库，点击「Settings」
2. 左侧菜单找到「Secrets and variables」→「Actions」
3. 点击「New repository secret」，添加以下 6 个 Secrets：

| Name | Secret | 说明 |
|------|---|------|
| `SWJTU_USERNAME` | 你的学号 | 教务系统登录学号 |
| `SWJTU_PASSWORD` | 你的密码 | 教务系统登录密码 |
| `SMTP_HOST` | smtp.qq.com | 邮箱 SMTP 服务器地址 |
| `NOTIFY_EMAIL` | your@qq.com | 接收通知的邮箱 |
| `EMAIL_PASSWORD` | 授权码 | 邮箱授权码（不是邮箱密码） |
| `GIST_PAT` | ghp_xxx... | GitHub Personal Access Token |

**添加方式：**
- 在「Name」输入框填入 Secret 名称（如 `SWJTU_USERNAME`）
- 在「Secret」输入框填入对应的值
- 点击「Add secret」
- 重复以上步骤添加所有 6 个 Secrets

### 步骤 3：启用 GitHub Actions

1. **进入 Actions 页面**
   - 点击仓库顶部的「Actions」标签

2. **启用 Workflows**
   - 如果看到提示「Workflows aren't being run on this forked repository」
   - 点击「I understand my workflows, go ahead and enable them」

3. **确认 Monitor Scores 工作流已启用**
   - 在左侧列表中找到「Monitor Scores」
   - 确保它处于启用状态
   - （别的workflow我用作测试，不用管）

### 步骤 4：手动测试运行

1. **在 Actions 页面**，点击左侧的「Monitor Scores」

2. **手动触发运行**
   - 点击右上角「Run workflow」下拉按钮
   - 点击「Run workflow」确认

3. **查看运行结果**
   - 刷新页面会看到正在运行的 workflow
   - 点击正在运行的任务，再点击run-job，查看实时日志
   - 展开Run Script日志，如果配置正确，应该能看到：
     ```
     --- 任务开始: 监控成绩变化 ---
     正在从数据库获取历史成绩...
     正在登录教务系统获取最新成绩...
     --- 登录尝试 #1/10 ---
     正在获取验证码...
     OCR 识别结果: xxxx
     正在尝试登录API...
     API验证成功！
     ...
     ```
   - **该运行结果也只有你可见**

4. **检查邮箱**
   - 如果是首次运行，你会收到带有你所有成绩的邮件；如果有成绩变化，你也会收到邮件通知

## 四、常见问题

### Q1：登录失败怎么办？

**可能原因：**
1. 学号或密码错误
   - 检查 `SWJTU_USERNAME` 和 `SWJTU_PASSWORD` 是否正确
   
2. 教务系统维护或关闭外网访问
   - 查看运行日志，如果多次重试都失败
   - 尝试在浏览器手动登录教务系统确认
   
3. 验证码识别失败
   - 项目使用 OCR 自动识别验证码
   - 最多重试 10 次，偶尔失败是正常的
   - 如果持续失败，等待下次自动运行

### Q2：收不到邮件通知？

**检查清单：**

1. **Secrets 配置是否正确**
   - 确认 `SMTP_HOST`、`NOTIFY_EMAIL`、`EMAIL_PASSWORD` 都已配置
   - 确认 `EMAIL_PASSWORD` 使用的是授权码，不是登录密码

2. **检查垃圾邮件箱**
   - 第一次接收时可能被识别为垃圾邮件

3. **查看运行日志**
   - 进入 Actions 查看详细日志
   - 搜索「邮件」或「SMTP」相关错误信息

4. **SMTP 服务是否开启**
   - 确认邮箱已开启 SMTP 服务
   - QQ 邮箱：设置 → 账户 → POP3/SMTP 服务

5. **端口问题**
   - 项目默认使用 465 端口
   - 如需修改，可在 Secrets 中添加 `SMTP_PORT`

### Q3：如何查看当前存储的成绩数据？

1. 访问你的 GitHub Gists：https://gist.github.com/你的github用户名
2. 找到描述为 `just_for_swjtu_scores_monitor` 的 Gist
3. 文件名为 `scores.json`
4. 点击查看即可看到存储的成绩 JSON 数据

### Q4：GitHub Actions 免费额度够用吗？

**免费账户限制：**
- 每月 2000 分钟运行时间
- 公开仓库不消耗额度
- 私有仓库消耗额度

**本项目消耗：**
- 单次运行约 30s
- 每天运行约 54 次（20分钟间隔，18小时）
- 每月约 54 × 30 × 0.5 = 810 分钟

**建议：**
- 保持仓库为公开（Public）→ 不消耗额度

### Q5：为什么有时候运行失败？

**正常情况：**
- 验证码识别失败：会自动重试 10 次
- 教务系统临时无法访问：下次运行会自动恢复
- GitHub Actions 服务波动：偶尔发生

**不影响使用：**
- 只要不是连续多次失败，都属于正常现象
- 20 分钟后会自动重新运行

### Q6：如何更新项目代码？

如果原项目有更新，同步到你的 Fork：

1. 在你的仓库页面，点击「Sync fork」
2. 点击「Update branch」
3. Secrets 配置会保留，无需重新配置

### Q7：可以监控多个账号吗？

当前版本只支持单账号。如需监控多个账号：

1. 再次 Fork 项目（使用不同的仓库名）
2. 为每个仓库配置不同的 Secrets
3. 每个仓库独立运行

---
# 接下来是与项目部署使用无关的内容，可以选择性阅读

## 五、monitor.yml 工作原理

### 运行时间

```yaml
schedule:
  - cron: '*/20 0-15,22-23 * * *'
```

- **北京时间**：6:00 - 23:59，每 20 分钟运行一次
- **UTC时间**：22:00 - 15:59（GitHub Actions 使用 UTC 时间）
- 北京时间 00:00 - 5:59 教务处暂停外部访问，故不运行
- 由于 GitHub Actions 调度原因，时间可能偏移最多 15 分钟

### 工作流程

1. **检出代码**：获取最新的项目代码
2. **安装依赖**：使用 uv 安装 Python 依赖
3. **运行监控脚本**：
   - 从 GitHub Gist 读取上次保存的成绩
   - 登录教务系统获取最新成绩
   - 对比新旧成绩，检测变化
   - 如果有变化，发送邮件通知
   - 将最新成绩保存到 Gist

### 检测的变化类型

- 新增课程成绩
- 成绩分数变化
- 新增平时成绩
- 平时成绩变化


## 六、使用与维护

### 查看运行日志

1. 进入仓库的「Actions」页面
2. 点击任意一次运行记录
3. 点击「run-job」查看详细日志
4. 可以看到登录过程、成绩获取、变化检测等详细信息

### 手动触发监控

1. 进入「Actions」→「Monitor Scores」
2. 点击「Run workflow」
3. 点击「Run workflow」确认
4. 适合测试或立即检查成绩

### 修改监控频率

编辑 `.github/workflows/monitor.yml`，修改 cron 表达式：

```yaml
# 每10分钟
- cron: '*/10 0-15,22-23 * * *'

# 每小时
- cron: '0 0-15,22-23 * * *'
```

**注意**：过于频繁可能被教务系统限制访问

### 暂停监控

1. 进入「Actions」→「Monitor Scores」
2. 点击右上角「...」菜单
3. 选择「Disable workflow」

### 恢复监控

重新启用 workflow 即可


## 七、技术说明

### 使用的技术栈

- **Python 3.12**：主要编程语言
- **uv**：快速的 Python 包管理器
- **requests + BeautifulSoup**：网页抓取
- **OCR 验证码识别**：自动识别登录验证码
- **GitHub Gist**：数据存储
- **SMTP**：邮件发送

### 项目结构

```
.github/workflows/
  └── monitor.yml          # GitHub Actions 工作流配置
actions/
  └── index.py             # 主要业务逻辑
utils/
  ├── fetcher.py          # 教务系统爬虫
  ├── database.py         # Gist 数据存储
  ├── notify.py           # 邮件通知
  └── ocr.py              # 验证码识别
```

## 八、Gist 数据存储说明

### 什么是 Gist？

GitHub Gist 是 GitHub 提供的代码片段托管服务，本项目使用它来存储你的成绩数据。每次运行时，程序会从 Gist 读取上次的成绩，对比后将最新成绩写回 Gist。

### Gist 的创建与管理

- **自动创建**：首次运行时，程序会自动创建一个名为 `swjtu_scores_data` 的 **私有 Gist**
- **文件名**：`scores.json`
- **Gist 描述**：`just_for_swjtu_scores_monitor`
- **访问权限**：只有你自己（通过 GIST_PAT）可以访问

### 如何查看 Gist 数据？

1. 访问 https://gist.github.com/你的用户名
2. 找到描述为 `just_for_swjtu_scores_monitor` 的 Gist
3. 点击查看 `scores.json` 文件内容

### 如何删除 Gist 数据（重置）？

如果你想重置成绩监控（比如清空历史数据重新开始）：

1. 访问 https://gist.github.com/你的用户名
2. 找到并点击描述为 `just_for_swjtu_scores_monitor` 的 Gist
3. 点击右上角「Delete」按钮删除
4. 下次运行时，程序会自动创建新的 Gist

### Gist 数据格式

存储的 JSON 数据格式如下：

```json
{
  "课程名称1": {
    "score": "85",
    "daily_scores": ["90", "88", "92"]
  },
  "课程名称2": {
    "score": "90",
    "daily_scores": []
  }
}
```

- `score`：期末/总评成绩
- `daily_scores`：平时成绩列表


## 九、OCR 验证码识别说明

### 为什么需要 OCR？

教务系统登录需要输入图形验证码，本项目机缘巧合下选择自己做 OCR 模块自动识别验证码，无需调用第三方 API，完全本地运行。

### OCR 工作原理

识别流程分为三个主要步骤：

1. **图像预处理**
   - 灰度化：将彩色验证码转为灰度图像
   - 二值化：将灰度图像转为黑白二值图像（阈值 94）
   - 去噪：消除干扰线和噪点

2. **字符分割**
   - 垂直投影分析：统计每列的黑色像素数量
   - 边界检测：找到每个字符的左右边界
   - 裁剪提取：将每个字符单独切割出来

3. **模板匹配**
   - 加载预制模板库（`utils/templates/` 目录）
   - 滑动窗口比对：允许 ±3 像素偏移
   - 像素级相似度计算：选择最匹配的字符

### 模板库

模板文件存放在 `utils/templates/` 目录下：
- 每个字符对应一个 PNG 文件
- 文件名即为字符内容
- 模板来源于实际验证码样本

### 识别准确率

- 程序会自动重试最多 **10 次**
- 综合成功率较高

### 识别失败怎么办？

如果遇到持续识别失败：

1. **等待自动重试**：程序会自动重试 10 次
2. **等待下次运行**：20 分钟后会自动重新运行
3. **检查日志**：查看 Actions 日志中的 OCR 识别结果

### 调试模式（开发者）

如需调试 OCR，可在本地运行时启用调试输出：
- 调试文件保存在 `utils/debug_output/` 目录
- 包含二值化结果、垂直投影图、分割字符等中间结果

## 十、邮件成绩通知说明

### 通知触发条件

以下情况会触发邮件通知：

- **新增课程成绩**：检测到之前没有的课程出现成绩
- **成绩分数变化**：已有课程的成绩发生变更
- **新增平时成绩**：检测到新的平时成绩记录
- **平时成绩变化**：已有平时成绩发生变更
- **首次运行**：第一次运行时会发送当前所有成绩

### 邮件格式

通知邮件采用 HTML 格式，包含：

- **成绩变化表格**：清晰展示课程名称和对应成绩
- **成绩高亮**：新成绩用醒目颜色标注
- **变化说明**：标注是新增还是更新

### 邮件发送配置

| 配置项 | 说明 |
|--------|------|
| `SMTP_HOST` | 邮件服务器地址（如 `smtp.qq.com`） |
| `NOTIFY_EMAIL` | 发送和接收邮件的邮箱地址 |
| `EMAIL_PASSWORD` | 邮箱授权码（非登录密码） |
| `SMTP_PORT` | 可选，默认 465（SSL 加密） |

### 支持的邮箱

理论上支持所有开启 SMTP 服务的邮箱。

### 收不到邮件？

1. **检查垃圾邮件箱**：首次接收可能被标记为垃圾邮件
2. **确认授权码正确**：使用邮箱授权码，而非登录密码
3. **确认 SMTP 已开启**：在邮箱设置中开启 SMTP 服务
4. **查看运行日志**：Actions 日志会显示邮件发送状态

### 自定义端口

如需使用非默认端口（如 587），可添加 Secret：
- **Name**: `SMTP_PORT`
- **Secret**: `587`

## 十一、致谢与支持

如果这个项目对你有帮助，欢迎：

- ⭐ Star 本项目
- 🐛 提交 Issue 反馈问题
- 🔀 提交 Pull Request 改进项目


