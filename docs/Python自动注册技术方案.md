# Python 自动注册技术方案

## 方案概述

基于 **Python + CDP + 临时邮箱 API** 的全自动网站账号注册方案。核心思路是三个协议的配合：

| 协议 | 用途 |
|------|------|
| **CDP**（Chrome DevTools Protocol） | 控制浏览器，模拟用户操作 |
| **HTTPS** | 与目标网站交互 |
| **REST API** | 通过 Mail.tm 收取验证邮件 |

Python 作为中间调度层，串联起整个流程。

---

## 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 语言 | Python 3.x | 中间调度层 |
| 浏览器控制 | CDP (Chrome DevTools Protocol) | WebSocket 连接 Chrome |
| 临时邮箱 | Mail.tm REST API | 创建临时邮箱、接收验证邮件 |
| 指纹伪装 | JS 注入 | 通过 CDP 注入反检测脚本 |
| 验证码 | 正则提取 | 从邮件中提取验证链接 |

---

## 完整执行流程

```mermaid
graph LR
    subgraph Step1["Step 1: 初始化"]
        A1[创建临时邮箱]
        A2[Mail.tm API]
        A3[获取 Token]
    end

    subgraph Step2["Step 2: 注册"]
        B1[打开注册页面]
        B2[注入指纹伪装]
        B3[模拟人类填写]
        B4[提交注册表单]
    end

    subgraph Step3["Step 3: 验证"]
        C1[轮询 Mail.tm]
        C2[读取验证邮件]
        C3[正则提取链接]
        C4[访问验证 URL]
    end

    Step1 -->|POST /accounts\nPOST /token| Step2
    Step2 -->|CDP: Page.navigate\nCDP: DOM.querySelector\nCDP: Input.dispatch*\nCDP: Page.addScript| Step3

    style Step1 fill:#0f3460,stroke:#e94560,color:#fff
    style Step2 fill:#1a3a5c,stroke:#e94560,color:#fff
    style Step3 fill:#1e4d6b,stroke:#e94560,color:#fff
```

---

## 四、各步骤详细说明

### Step 1：初始化 — 创建临时邮箱

**目标：** 获取一个可用的临时邮箱地址和访问 Token。

**API 调用：**

```
POST https://api.mail.tm/accounts
Body: { "address": "<随机用户名>@<可用域名>", "password": "<密码>" }

POST https://api.mail.tm/token
Body: { "address": "<邮箱地址>", "password": "<密码>" }
```

**数据流：**

```
Python → HTTPS → Mail.tm API → 返回邮箱地址 + Token
```

**输出：** 临时邮箱地址、JWT Token

---

### Step 2：注册 — 模拟用户填写表单

**目标：** 在目标网站完成注册表单的填写和提交。

**CDP 命令序列：**

| 序号 | CDP 方法 | 用途 |
|------|----------|------|
| 1 | `Page.addScriptToEvaluateOnNewDocument` | 注入指纹伪装脚本 |
| 2 | `Page.navigate` | 打开目标注册页面 |
| 3 | `DOM.querySelector` | 定位表单输入框 |
| 4 | `Input.dispatchKeyEvent` | 模拟键盘输入 |
| 5 | `Input.dispatchMouseEvent` | 模拟鼠标点击提交 |

**数据流：**

```
页面控制：Python → WebSocket(CDP) → Chrome → HTTPS → 目标网站
指纹注入：Python → CDP(Page.addScriptToEvaluateOnNewDocument) → Chrome JS引擎
```

**关键点：**
- 指纹伪装脚本需在页面加载前注入
- 输入操作需模拟人类行为（随机延迟、逐字输入）
- 使用 `Input.dispatch*` 而非直接修改 DOM 值

---

### Step 3：验证 — 获取并访问验证链接

**目标：** 从临时邮箱获取验证邮件，提取验证链接并访问完成注册。

**API 调用：**

```
GET https://api.mail.tm/messages
Headers: { "Authorization": "Bearer <token>" }

GET https://api.mail.tm/messages/{id}
Headers: { "Authorization": "Bearer <token>" }
```

**数据流：**

```
邮件读取：Python → HTTPS → Mail.tm API → 返回邮件内容
链接验证：Python → CDP(Page.navigate) → Chrome → HTTPS → 目标网站验证接口
```

**关键点：**
- 需要轮询等待邮件到达（设置超时机制）
- 使用正则表达式从邮件 HTML 中提取验证链接
- 通过 CDP 控制浏览器访问验证链接

---

## 五、数据流总览

```mermaid
graph TD
    Python["🐍 Python 调度层"]

    Python -->|HTTPS| MailAPI["📧 Mail.tm API\n邮箱创建 / 邮件读取"]
    Python -->|WebSocket CDP| Chrome["🌐 Chrome 浏览器"]
    Python -->|正则解析| Extract["🔗 提取验证链接"]

    Chrome -->|HTTPS| Target["🎯 目标网站"]
    Chrome --- JS["JS引擎\n指纹伪装脚本"]
    Chrome --- DOM["DOM 操作\n表单填写"]
    Chrome --- Nav["页面导航\n验证链接"]

    style Python fill:#e94560,stroke:#fff,color:#fff
    style MailAPI fill:#0f3460,stroke:#53d8fb,color:#fff
    style Chrome fill:#1a3a5c,stroke:#53d8fb,color:#fff
    style Target fill:#1e4d6b,stroke:#53d8fb,color:#fff
    style Extract fill:#0f3460,stroke:#53d8fb,color:#fff
    style JS fill:#16213e,stroke:#a8b2d1,color:#a8b2d1
    style DOM fill:#16213e,stroke:#a8b2d1,color:#a8b2d1
    style Nav fill:#16213e,stroke:#a8b2d1,color:#a8b2d1
```

| 步骤 | 数据流 |
|------|--------|
| 邮箱创建 | `Python → HTTPS → Mail.tm API → 返回邮箱地址 + Token` |
| 页面控制 | `Python → WebSocket(CDP) → Chrome → HTTPS → 目标网站` |
| 指纹注入 | `Python → CDP(Page.addScriptToEvaluateOnNewDocument) → Chrome JS引擎` |
| 邮件读取 | `Python → HTTPS → Mail.tm API → 返回邮件内容` |
| 链接验证 | `Python → CDP(Page.navigate) → Chrome → HTTPS → 目标网站验证接口` |

---

## 六、核心协议配合

```mermaid
graph TB
    PY["Python 调度层"] --> CDP["CDP 协议\n(WebSocket)"]
    PY --> HTTPS["HTTPS"]
    PY --> REST["REST API\n(Mail.tm)"]

    CDP --> CDP1["· 控制浏览器"]
    CDP --> CDP2["· 注入脚本"]
    CDP --> CDP3["· 模拟输入"]

    HTTPS --> H1["· 网站交互"]
    HTTPS --> H2["· 页面加载"]
    HTTPS --> H3["· 验证请求"]

    REST --> R1["· 创建邮箱"]
    REST --> R2["· 收取邮件"]
    REST --> R3["· 读取内容"]

    style PY fill:#e94560,stroke:#fff,color:#fff
    style CDP fill:#0f3460,stroke:#53d8fb,color:#fff
    style HTTPS fill:#0f3460,stroke:#53d8fb,color:#fff
    style REST fill:#0f3460,stroke:#53d8fb,color:#fff
```

---

## 七、关键技术要点

### 7.1 指纹伪装

通过 `Page.addScriptToEvaluateOnNewDocument` 在页面加载前注入 JS 脚本，覆盖浏览器指纹信息：

- `navigator.webdriver` → `false`
- `navigator.plugins` → 模拟真实插件列表
- Canvas / WebGL 指纹随机化
- `window.chrome` 属性伪装

### 7.2 人类行为模拟

- **输入延迟：** 每个按键之间添加 50-150ms 随机延迟
- **鼠标移动：** 贝塞尔曲线模拟自然移动轨迹
- **操作间隔：** 各步骤之间添加随机等待时间

### 7.3 邮件轮询策略

```
最大等待时间: 60s
轮询间隔: 3-5s
超时处理: 重试或标记失败
```

---

## 八、风险与注意事项

| 风险 | 应对措施 |
|------|----------|
| IP 封禁 | 使用代理池轮换 IP |
| 验证码 | 接入打码平台或 AI 识别 |
| 指纹检测 | 定期更新伪装脚本 |
| 邮箱服务不可用 | 备用临时邮箱服务 |
| 注册频率限制 | 控制注册速度，添加随机延迟 |

---

## 附录：Mermaid 支持的图表类型

> 以下图表类型均可在飞书文档的代码块中使用（语言选择 `Mermaid`）。

### 1. 流程图（Flowchart）

适用场景：步骤流程、决策分支、系统架构

```mermaid
graph LR
    A[开始] --> B{条件判断}
    B -->|是| C[执行操作]
    B -->|否| D[跳过]
    C --> E[结束]
    D --> E
```

### 2. 时序图（Sequence Diagram）

适用场景：API 调用顺序、组件间交互、通信协议

```mermaid
sequenceDiagram
    participant P as Python
    participant M as Mail.tm
    participant C as Chrome
    participant T as 目标网站

    P->>M: POST /accounts (创建邮箱)
    M-->>P: 返回邮箱地址
    P->>M: POST /token (获取令牌)
    M-->>P: 返回 JWT Token
    P->>C: CDP: Page.addScript (注入指纹伪装)
    P->>C: CDP: Page.navigate (打开注册页)
    C->>T: HTTPS 请求注册页面
    T-->>C: 返回页面内容
    P->>C: CDP: Input.dispatch* (模拟填写)
    P->>C: CDP: 点击提交
    C->>T: POST 注册表单
    T-->>C: 注册成功，发送验证邮件
    loop 轮询等待邮件
        P->>M: GET /messages
        M-->>P: 邮件列表
    end
    P->>M: GET /messages/{id}
    M-->>P: 邮件内容 (含验证链接)
    P->>C: CDP: Page.navigate (访问验证链接)
    C->>T: HTTPS 验证请求
    T-->>C: 验证完成
```

### 3. 类图（Class Diagram）

适用场景：面向对象设计、数据模型、接口定义

```mermaid
classDiagram
    class AutoRegister {
        -email: str
        -token: str
        -browser: Browser
        +run()
    }
    class MailClient {
        +create_account()
        +get_token()
        +poll_messages()
    }
    class BrowserController {
        +navigate(url)
        +inject_script(js)
        +fill_form(data)
    }
    AutoRegister --> MailClient
    AutoRegister --> BrowserController
```

### 4. 状态图（State Diagram）

适用场景：状态机、对象生命周期、任务状态流转

```mermaid
stateDiagram-v2
    [*] --> 初始化
    初始化 --> 邮箱已创建: 创建成功
    初始化 --> 失败: 创建失败
    邮箱已创建 --> 注册中: 打开注册页
    注册中 --> 待验证: 提交表单
    注册中 --> 失败: 表单提交失败
    待验证 --> 已完成: 验证链接访问成功
    待验证 --> 失败: 超时未收到邮件
    失败 --> [*]
    已完成 --> [*]
```

### 5. 甘特图（Gantt）

适用场景：项目排期、任务时间规划、里程碑管理

```mermaid
gantt
    title 自动注册流程耗时
    dateFormat ss
    axisFormat %S秒

    section 初始化
    创建邮箱        :a1, 00, 2s
    获取 Token      :a2, after a1, 1s

    section 注册
    注入指纹伪装     :b1, after a2, 1s
    打开注册页面     :b2, after b1, 3s
    模拟填写表单     :b3, after b2, 5s
    提交注册        :b4, after b3, 2s

    section 验证
    轮询等待邮件     :c1, after b4, 10s
    提取验证链接     :c2, after c1, 1s
    访问验证 URL    :c3, after c2, 2s
```

### 6. 饼图（Pie Chart）

适用场景：比例分布、占比统计

```mermaid
pie title 注册流程耗时占比
    "初始化 (邮箱创建)" : 10
    "页面加载与填写" : 35
    "等待验证邮件" : 45
    "验证完成" : 10
```

### 7. ER 图（Entity Relationship Diagram）

适用场景：数据库表关系、数据结构设计

```mermaid
erDiagram
    ACCOUNT ||--o{ EMAIL : has
    ACCOUNT {
        string username
        string password
        string status
    }
    EMAIL {
        string address
        string token
        datetime created_at
    }
    EMAIL ||--o{ MESSAGE : receives
    MESSAGE {
        string subject
        string body
        string verification_link
    }
```

### 8. 思维导图（Mindmap）

适用场景：知识结构梳理、头脑风暴、技术拆解

```mermaid
mindmap
  root((自动注册方案))
    初始化
      Mail.tm API
      创建邮箱
      获取 Token
    注册
      CDP 控制浏览器
        Page.navigate
        DOM.querySelector
        Input.dispatch
      指纹伪装
        navigator.webdriver
        Canvas 指纹
        WebGL 指纹
      人类行为模拟
        随机延迟
        贝塞尔曲线鼠标
    验证
      轮询邮件
      正则提取链接
      访问验证 URL
    风险应对
      代理池
      打码平台
      频率控制
```

### 9. 时间线（Timeline）

适用场景：项目里程碑、版本演进历史

```mermaid
timeline
    title 项目开发里程碑
    第1周 : 技术调研
           : Mail.tm API 对接
    第2周 : CDP 浏览器控制
           : 指纹伪装实现
    第3周 : 表单填写自动化
           : 验证流程打通
    第4周 : 异常处理与重试
           : 代理池集成
           : v1.0 发布
```

### 图表类型速查表

| 类型 | 语法关键字 | 适用场景 |
|------|----------|---------|
| 流程图 | `graph` / `flowchart` | 步骤流程、决策分支 |
| 时序图 | `sequenceDiagram` | API 调用顺序、组件交互 |
| 类图 | `classDiagram` | 面向对象设计、数据模型 |
| 状态图 | `stateDiagram-v2` | 状态机、生命周期 |
| 甘特图 | `gantt` | 项目排期、时间规划 |
| 饼图 | `pie` | 比例分布 |
| ER 图 | `erDiagram` | 数据库表关系 |
| 思维导图 | `mindmap` | 知识结构、头脑风暴 |
| 时间线 | `timeline` | 里程碑、版本演进 |
| 桑基图 | `sankey-beta` | 数据流向、资源分配 |
| 框图 | `block-beta` | 系统架构、模块组成 |
