# AIOps Agent

面向企业知识问答和智能运维排障的 FastAPI 应用。项目集成 RAG 知识库、Milvus 向量检索、LangChain/LangGraph Agent、MCP 工具调用和一个轻量 Web 聊天界面。


## 功能

- RAG 问答：上传 Markdown / TXT 文档后自动切分、向量化并写入 Milvus。
- 流式对话：支持普通响应和 SSE 流式输出。
- AIOps 诊断：基于 Plan-Execute-Replan 流程调用日志/监控 MCP 工具生成排障报告。
- Web 控制台：纯静态前端，支持会话历史、文档上传、Markdown 渲染和代码高亮。
- 可配置安全默认值：CORS 白名单、上传扩展名、上传大小和上传目录可通过环境变量控制。

## 技术栈

- Backend: FastAPI, Pydantic Settings, Loguru
- Agent/RAG: LangChain, LangGraph, DashScope, Milvus
- Tooling: MCP / FastMCP
- Frontend: HTML, CSS, vanilla JavaScript
- Runtime: Python 3.11+

## 项目结构

```text
app/
  api/          # HTTP API
  agent/        # AIOps Agent 编排
  core/         # LLM 和 Milvus 客户端
  models/       # Pydantic 模型
  services/     # RAG、向量索引、文档切分等业务逻辑
  tools/        # Agent 工具
  utils/        # 日志和上传校验工具
static/         # Web 前端
mcp_servers/    # 日志查询和监控 MCP 服务
aiops-docs/     # 示例知识库文档
tests/          # 单元测试
```

## 快速开始

1. 创建环境并安装依赖：

```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

2. 准备配置：

```bash
cp .env.example .env
```

编辑 `.env`，至少填写 `DASHSCOPE_API_KEY`。

3. 启动 Milvus：

```bash
docker compose -f vector-database.yml up -d
```

4. 启动 MCP 服务：

```bash
python mcp_servers/cls_server.py
python mcp_servers/monitor_server.py
```

5. 启动主服务：

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 9900
```

访问：

- Web UI: <http://localhost:9900>
- API Docs: <http://localhost:9900/docs>
- Health: <http://localhost:9900/health>

Windows 用户也可以使用：

```powershell
.\start-windows.bat
.\stop-windows.bat
```
