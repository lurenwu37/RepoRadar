[🇨🇳 中文](README.zh.md) | **🇺🇸 English**

# GitHub Hot Repositories Radar 🚀

An automated Python-based GitHub trending and hot repositories radar. It fetches the most starred repositories created within a specific date range, evaluates and scores them using the Agnes LLM, summarizes them into a structured dual-dimension recommended list ("What it is" and "What it does / Use cases"), and pushes highly readable interactive cards to your Feishu (Lark) group chats.

---

## 🌟 Key Features

- **Multi-interval Reports**:
  - **Daily Report (`index.py`)**: Monitors newly created repositories from yesterday, scoring and selecting the Top 5.
  - **Weekly Report (`weekly_report.py`)**: Summarizes the past 7 days of top-starred creations.
  - **Monthly Report (`monthly_report.py`)**: Summarizes the past 30 days of top-starred creations.
- **Parametrized Shared Fetcher**: Shared `fetcher.py` handles flexible datetime window queries to the GitHub Search API.
- **Feishu Interactive Card Delivery**: Clean structure utilizing `div` and `lark_md` components, delivering a clear title, link, star counts, and bulleted highlights.
- **Agnes LLM Integration**: Uses Agnes LLM (OpenAI-compatible endpoints) to intelligently analyze and synthesize repository purposes and practical values.
- **Zero-Dependency Dotenv Loading**: Recursively locates and loads environment configurations automatically.

---

## 📁 Project Structure

```text
.
├── AGENTS.md                  # Project development guidelines
├── config.yml                 # General config metadata
├── README.md                  # English documentation
├── README.zh.md               # Chinese documentation
├── .env.example               # Environment variables template
└── src
    └── zhoubaobot
        ├── .env               # Your local configuration (Ignored by git)
        ├── feishu.py          # Feishu message sender & card template builder
        ├── fetcher.py         # GitHub API trending repositories collector
        ├── index.py           # Daily report runner entrypoint
        ├── monthly_report.py  # Monthly report runner entrypoint
        ├── prompt.txt         # Prompt file for LLM scoring & summarization
        ├── scorer.py          # LLM connection, scoring parser & fallback scorer
        └── weekly_report.py   # Weekly report runner entrypoint
```

---

## 🛠️ Environment Configuration

Copy the `.env.example` template to `src/zhoubaobot/.env` and fill in your keys:

```bash
cp .env.example src/zhoubaobot/.env
```

Open `src/zhoubaobot/.env` and update the following:

- **`FEISHU_WEBHOOK_URL`**: Your Feishu bot's Webhook URL.
- **`AGNES_API_KEY`**: Your Agnes LLM API Key (can fallback to DeepSeek or OpenAI keys).
- **`AGNES_API_BASE`**: Endpoint URL (default is `https://api.deepseek.com/v1`).
- **`AGNES_MODEL`**: Model model identifier (default is `deepseek-chat`).
- **`GITHUB_TOKEN`**: Highly recommended to prevent GitHub Search API 403 Rate Limit blocks.

---

## 🚀 Execution & Usage

Navigate to the source directory:

```bash
cd src/RepoRadar
```

### 1. Daily Report
```bash
python3 index.py
```
### 2. Weekly Report
```bash
python3 weekly_report.py
```
### 3. Monthly Report
```bash
python3 monthly_report.py
```

---

## 🤖 Automating with GitHub Actions + Cron-Job.org

Instead of managing a local cron job daemon, you can trigger this repository seamlessly on a schedule using **GitHub Actions** triggered by **cron-job.org** (or built-in GitHub Schedule events).

### Method A: Built-in GitHub Actions Schedule (Simplest)

Create a GitHub workflow file under `.github/workflows/radar.yml`:

```yaml
name: GitHub Hot Repositories Radar

on:
  schedule:
    # Daily at 01:00 UTC
    - cron: '0 1 * * *'
  workflow_dispatch: # Allows manual trigger

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

Save your credentials under **Settings -> Secrets and variables -> Actions** in your GitHub repository.

### Method B: Cron-Job.org Trigger (For Custom Dynamic Control)

If you prefer externalized triggers from **cron-job.org** to ping your actions workflow dynamically:

1. Register or log in to [cron-job.org](https://cron-job.org/).
2. Setup a GitHub Personal Access Token (PAT) with `workflow` dispatch permission.
3. Configure a job in cron-job.org with the following parameters:
   - **URL**: `https://api.github.com/repos/{owner}/{repo}/actions/workflows/radar.yml/dispatches`
   - **Request Method**: `POST`
   - **Request Headers**:
     - `Accept: application/vnd.github+json`
     - `Authorization: Bearer <YOUR_GITHUB_PAT>`
     - `User-Agent: Cron-Job-Bot`
   - **Request Body** (JSON):
     ```json
     {
       "ref": "main"
     }
     ```
4. Define your preferred execution time (e.g. daily, weekly, monthly) and cron-job.org will invoke the workflow accordingly.
