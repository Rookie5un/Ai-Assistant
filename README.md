# Ai Assistant Web

一个基于 `Vue 3 + FastAPI` 的 AI 助手 Web MVP，包含：

- 登录与演示账号
- 工作台概览
- 流式聊天界面
- OpenAI 真实模型接入
- 助手管理
- 知识库与文档上传
- 本地 SQLite 默认启动
- PostgreSQL `docker-compose` 开发入口

## 目录结构

```text
.
├── backend
│   ├── app
│   └── requirements.txt
├── frontend
│   ├── src
│   └── package.json
├── docker-compose.yml
├── PRD.md
└── README.md
```

## 后端启动

默认使用 SQLite，不要求你先装 PostgreSQL。

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

服务地址：`http://localhost:8000`

默认演示账号：

- 邮箱：`demo@aicontrol.dev`
- 密码：`Demo123456!`

如果要启用真实模型，在项目根目录新建 `.env`。你现在可以接 `OpenAI`、`千问 / 百炼`、`豆包 / 方舟`，任选其一或同时配置。

OpenAI：

```text
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
```

千问 / 百炼：

```text
QWEN_API_KEY=your_dashscope_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1
QWEN_MODEL=qwen3.5-plus
```

豆包 / 方舟：

```text
DOUBAO_API_KEY=your_ark_key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-1-6-251015
```

如果你使用兼容 OpenAI 的网关，也可以继续按下面方式覆写：

```text
OPENAI_BASE_URL=https://your-compatible-endpoint/v1
```

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端地址：`http://localhost:5173`

## PostgreSQL 开发环境

如果你想切到 PostgreSQL：

1. 复制环境变量

```bash
cp .env.example .env
```

2. 启动数据库

```bash
docker compose up -d postgres
```

3. 把 `.env` 里的 `DATABASE_URL` 改成：

```text
DATABASE_URL=postgresql+psycopg://ai_user:ai_password@localhost:5432/ai_assistant
```

4. 重新启动后端

## 当前实现说明

- 聊天接口已接好 `SSE` 流式返回
- 知识库支持 `PDF / DOCX / TXT / Markdown` 上传
- 文档会做基础切片与关键词检索
- 当前聊天支持 `OpenAI / 千问 / 豆包` 三种 Provider
- 助手创建页可以为不同助手选择不同 Provider
- 如果某个 Provider 未配置 API Key，前端会明确提示缺少配置

## 下一步建议

你可以继续在这套骨架上补：

1. 接真实模型服务
2. 换成 PostgreSQL + Alembic
3. 增加消息重试、会话归档、助手编辑
4. 补管理员统计与用量审计




终端 1，启动后端：
```bash
cd "/Users/rookie/projects/Ai Assistant/backend"
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload


终端 2，启动前端：
```bash
cd "/Users/rookie/projects/Ai Assistant/frontend"
npm run dev -- --host 127.0.0.1 --port 5173
```
