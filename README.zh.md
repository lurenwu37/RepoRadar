**🇨🇳 中文** | [🇺🇸 English](README.md)

# GitHub 热门仓库雷达系统 🚀

基于 Python 实现的开源项目自动监控与雷达推荐系统。它动态抓取指定日期区间内创建且 Star 最多的 GitHub 仓库，通过 Agnes 大语言模型进行智能评估与打分，筛选出 Top 5 热门项目，并提取出直观的双维度总结（“这是什么”及“有什么用 / 适用场景”），最终通过飞书（Lark）互动消息卡片优雅地推送到你的群聊中。

---

## 🌟 核心功能

- **多时维度报告支持**：
  - **日报 (`index.py`)**：监测昨天新创建的热门仓库，筛选并推荐 Top 5 项目。
  - **周报 (`weekly_report.py`)**：总结过去 7 天内创建并最受欢迎的热门项目。
  - **月报 (`monthly_report.py`)**：盘点过去 30 天内最闪耀的全新开源项目。
- **参数化共享数据层**：利用公用的 `fetcher.py` 动态计算查询窗口（`created:START..END`），向 GitHub Search API 获取一手元数据。
- **飞书卡片级精美推送**：使用 `msg_type: interactive` 类型的卡片进行消息触达，配合 `div` 与 `lark_md` 模块，支持富文本链接、Emoji 以及双维度总结分栏排版。
- **Agnes 大模型强力支撑**：完美适配 Agnes 模型（兼容 OpenAI Chat Completions 接口），自动完成打分、降噪、合并，并具备本地关键词打分的备用降级逻辑。
- **零依赖配置加载**：脚本启动时自动向上层级递归搜索并加载 `.env` 配置文件，本地无缝运行。

---

## 📁 项目结构

```text
.
├── AGENTS.md                  # 开发规范与开发流程定义
├── config.yml                 # 全局基础配置参数
├── README.md                  # 英文项目文档
├── README.zh.md               # 中文项目说明文档
├── .env.example               # 环境参数配置模板文件
└── src
    └── zhoubaobot
        ├── .env               # 你的本地私密配置文件（Git 已忽略）
        ├── feishu.py          # 飞书卡片模板构建器及推送模块
        ├── fetcher.py         # 统一参数化 GitHub Search 数据抓取器
        ├── index.py           # 日报入口执行脚本
        ├── monthly_report.py  # 月报入口执行脚本
        ├── prompt.txt         # 供给大模型的打分与双维度总结 Prompt 提示词
        ├── scorer.py          # 模型调用、JSON 提取器与兜底打分器
        └── weekly_report.py   # 周报入口执行脚本
```

---

## 🛠️ 环境配置

首先将项目根目录下的配置文件模板 `.env.example` 复制到脚本工作目录中：

```bash
cp .env.example src/zhoubaobot/.env
```

编辑 `src/zhoubaobot/.env`，根据你的实际情况配置对应的 Key：

- **`FEISHU_WEBHOOK_URL`**：你的飞书机器人 Webhook 地址（如果有多个，可在 `FEISHU_WEBHOOK_URLS` 中用英文逗号分隔）。
- **`AGNES_API_KEY`**：你的 Agnes API 密钥（兼容 DeepSeek/OpenAI Key 格式）。
- **`AGNES_API_BASE`**：API 请求基地址（默认是 `https://api.deepseek.com/v1`）。
- **`AGNES_MODEL`**：具体大模型名称（默认是 `deepseek-chat`）。
- **`GITHUB_TOKEN`**：【强烈推荐】GitHub 个人访问令牌（PAT），仅需要 public_repo 读权限。如果不配置，GitHub API 会限制非认证 IP 每小时仅 60 次请求，极易触发 403。

---

## 🚀 运行与启动

进入运行文件夹中：

```bash
cd src/RepoRadar
```

### 1. 手动运行日报
```bash
python3 index.py
```
### 2. 手动运行周报
```bash
python3 weekly_report.py
```
### 3. 手动运行月报
```bash
python3 monthly_report.py
```

---

## 🤖 自动化托管：使用 GitHub Actions + Cron-Job.org

无需维护本地 Linux 服务器或常驻 Cron 进程，推荐使用免费的 **GitHub Actions** 来定时运行任务。你可以通过内置 Schedule 触发，或利用 **cron-job.org** 进行高自定义度外部触发。

### 方式 A：GitHub Actions 原生 Schedule 触发（最简便）

在你的 GitHub 仓库中，创建 `.github/workflows/radar.yml` 配置文件：

```yaml
name: GitHub Hot Repositories Radar

on:
  schedule:
    # 每天 UTC 时间 01:00 (北京时间早上 9点) 运行日报
    - cron: '0 1 * * *'
  workflow_dispatch: # 支持手动触发

jobs:
  run-radar:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install pyyaml

      - name: Run Radar
        env:
          FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
          AGNES_API_KEY: ${{ secrets.AGNES_API_KEY }}
          AGNES_API_BASE: ${{ secrets.AGNES_API_BASE }}
          AGNES_MODEL: ${{ secrets.AGNES_MODEL }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd src/zhoubaobot
          python3 index.py
```

将你的敏感环境变量保存在 GitHub 仓库的 **Settings -> Secrets and variables -> Actions** 密文管理中。

### 方式 B：使用 Cron-Job.org 外部触发（实现精准弹性控制）

若你希望利用外部服务 [cron-job.org](https://cron-job.org/) 进行实时且灵活的触发控制：

1. 登录并注册 [cron-job.org](https://cron-job.org/) 账户。
2. 创建一个拥有 `workflow` 触发权限的 GitHub 个人访问令牌（PAT）。
3. 在 cron-job.org 中新建定时任务：
   - **URL**：`https://api.github.com/repos/{owner}/{repo}/actions/workflows/radar.yml/dispatches`
   - **Request Method**：`POST`
   - **Request Headers**：
     - `Accept: application/vnd.github+json`
     - `Authorization: Bearer <你的_GITHUB_PAT>`
     - `User-Agent: Cron-Job-Bot`
   - **Request Body**（JSON 纯文本）：
     ```json
     {
       "ref": "main"
     }
     ```
4. 设定你的计划运行频率，cron-job.org 即可在计划时刻通过 API 精准唤醒你的 GitHub Actions 后台流并安全推送日报、周报或月报。
