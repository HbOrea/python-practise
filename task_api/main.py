from itertools import count
import time

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
import logging


app = FastAPI()

logger = logging.getLogger("uvicorn.access")


@app.get("/")
async def index():
    return "hello"

_next_id = count(1)  # 自增 ID 生成器
_store: dict[int, Task] = {}  #存储数据

class TaskCreate(BaseModel):
    title: str = Field(min_length=1)  # 标题不能为空

class Task(BaseModel):
    title: str
    done: bool | None = False
    id: int

def reset_store():
    """重置存储数据和自增 ID"""
    global _store, _next_id
    _store = {}
    _next_id = count(1)

@app.middleware("http")    
async def add_process_time_header(request, call_next):
    start_time = time.time()
    #将请求传递给下一个中间件或路由函数
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 记录请求信息
    logger.info(f"请求: {request.method} {request.url}")

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # 记录响应信息
    logger.info(
        f"响应: {request.method} {request.url} "
        f"状态码={response.status_code} 耗时={process_time:.3f}s"
    )

    return response

#实现 POST /tasks：输入 {"title":"学习 Python"}，生成自增 ID，返回 id/title/done。空白标题返回 422。
@app.post("/tasks", status_code=status.HTTP_201_CREATED, response_model=Task)
async def create_task(body: TaskCreate) -> Task:
    title = body.title
    if not title or title.strip() == "":
        raise HTTPException(422, "Title cannot be blank")
    task = Task(title=title, done=False, id=next(_next_id))
    _store[task.id] = task
    return task

@app.get("/tasks", response_model=list[Task])
async def list_tasks() -> list[Task]:
    return list(_store.values())

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int) -> Task:
    if task_id not in _store:
        raise HTTPException(404, "Task not found")
    return _store[task_id]