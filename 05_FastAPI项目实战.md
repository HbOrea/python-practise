# 阶段五：FastAPI 项目实战

> 目标：做一个可以本地运行、测试并逐步扩展到 AI/RAG 的任务 API。先用内存存储，避免把数据库配置问题混入基础练习。

## 环境与目录

建议 Python 3.11+。在空目录运行：

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
python -m pip install "fastapi" "uvicorn[standard]" "httpx" "pytest"
```

目录：

```text
task_api/
├── app.py
└── test_app.py
```

## 题目 1：创建任务接口

实现 `POST /tasks`：输入 `{"title":"学习 Python"}`，生成自增 ID，返回 `id/title/done`。空白标题返回 422。

## 题目 2：查询与完成任务

实现 `GET /tasks`、`GET /tasks/{id}` 和 `PATCH /tasks/{id}/done`。不存在返回 404。列表按创建顺序输出。

## 题目 3：异步模拟 AI 分析

实现 `POST /tasks/{id}/analyze`，模拟一次异步 I/O 分析，返回任务标题和一个固定建议；不要在协程中调用 `time.sleep`。

## 题目 4：为 API 编写测试

使用 FastAPI `TestClient` 编写创建成功、非法输入、404、标记完成、分析结果的测试；每个测试使用新数据容器。

## 参考实现：app.py（题目 1～3）

```python
import asyncio
from itertools import count

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Python Practice Task API")

class TaskCreate(BaseModel):
    title: str = Field(min_length=1)

class Task(BaseModel):
    id: int
    title: str
    done: bool = False

_store: dict[int, Task] = {}
_next_id = count(1)

def reset_store() -> None:
    global _next_id
    _store.clear()
    _next_id = count(1)

@app.post("/tasks", response_model=Task, status_code=201)
def create_task(body: TaskCreate) -> Task:
    title = body.title.strip()
    if not title:
        raise HTTPException(422, "title 不能为空")
    task = Task(id=next(_next_id), title=title)
    _store[task.id] = task
    return task

@app.get("/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return list(_store.values())

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    task = _store.get(task_id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    return task

@app.patch("/tasks/{task_id}/done", response_model=Task)
def mark_done(task_id: int) -> Task:
    task = get_task(task_id)
    task.done = True
    return task

@app.post("/tasks/{task_id}/analyze")
async def analyze_task(task_id: int) -> dict[str, str]:
    task = get_task(task_id)
    await asyncio.sleep(0.01)  # 用非阻塞等待模拟远程 I/O
    return {"title": task.title, "suggestion": "将大任务拆分成小步骤"}
```

启动服务：

```bash
uvicorn app:app --reload
```

浏览器访问 `http://127.0.0.1:8000/docs`，使用交互式 API 文档调试。

## 参考实现：test_app.py（题目 4）

```python
import pytest
from fastapi.testclient import TestClient
from app import app, reset_store

@pytest.fixture
def client():
    reset_store()
    with TestClient(app) as test_client:
        yield test_client

def test_create_and_list(client):
    response = client.post("/tasks", json={"title": "学习 Python"})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "title": "学习 Python", "done": False}
    assert len(client.get("/tasks").json()) == 1

def test_validation_and_missing(client):
    assert client.post("/tasks", json={"title": "  "}).status_code == 422
    assert client.get("/tasks/999").status_code == 404

def test_complete_and_analyze(client):
    task = client.post("/tasks", json={"title": "整理材料"}).json()
    task_id = task["id"]
    result = client.patch(f"/tasks/{task_id}/done")
    assert result.json()["done"] is True
    analysis = client.post(f"/tasks/{task_id}/analyze")
    assert analysis.status_code == 200
    assert analysis.json()["title"] == "整理材料"
```

测试命令：`python -m pytest -q`。

## 题目 5：从演示项目走向生产结构（设计题）

将 `app.py` 拆成 `api/routes/tasks.py`、`schemas/task.py`、`services/task_service.py`、`repositories/task_repository.py`。提出真实数据库下的并发、事务、测试隔离与配置管理方案。

### 参考思路

- Router 仅处理 HTTP 输入输出，Pydantic 模型放 schemas。
- Service 实现创建、完成、分析业务规则。
- Repository 负责数据访问，使用接口/Protocol 注入给 Service。
- 数据库存储使用 SQLAlchemy 2.x（异步方案可配合 `AsyncSession`），将数据库会话生命周期交给依赖注入，并正确提交/回滚事务。
- 使用 DB 自增主键或其他可靠 ID 方案，不能用单进程全局 `count` 保证多 worker 唯一性。
- 测试使用独立测试数据库/事务隔离，不依赖共享全局变量。
- AI 接口用 `httpx.AsyncClient` 发异步请求，并加超时、重试边界与并发限制；不要把模拟 `asyncio.sleep` 当成真实分析。

## 阶段验收

1. 能自己补充 `DELETE /tasks/{id}`。
2. 能实现 `GET /tasks?done=true`（可选过滤）。
3. 能写出至少 5 条 API 测试并通过。
4. 能解释内存存储不能用于多 worker 生产服务的原因。
5. 扩展挑战：用真实 LLM/RAG 服务替换 `/analyze` 中的模拟逻辑，并处理超时、错误和日志。
