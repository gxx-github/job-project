"""
FastAPI 后端 — 封装 LangGraph 工作流为 REST API + WebSocket
替代 CLI，提供 Web 界面所需的所有接口
"""
import os
import sys
import uuid
import json
import asyncio
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 确保项目根目录在 sys.path 中
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.graph import create_graph
from src.route import route_job_to_tech_stack
from src.tools.file_ops import read_tech_stack_tool
from src.memory.manager import memory_manager

load_dotenv()

app = FastAPI(title="AI 简历优化系统", version="1.0.0")

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会话存储
sessions: dict = {}

# 输出目录
OUTPUT_DIR = os.path.join(BASE_DIR, "Optimized_Output")
SESSION_DIR = os.path.join(BASE_DIR, "data", "sessions")


# ─── REST API ───────────────────────────────────────────────

@app.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)):
    """上传简历文件，返回 session_id"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".doc"):
        raise HTTPException(status_code=400, detail="仅支持 PDF/DOCX/DOC 格式")

    session_id = str(uuid.uuid4())[:8]
    session_path = os.path.join(SESSION_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)

    file_path = os.path.join(session_path, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    sessions[session_id] = {
        "resume_path": file_path,
        "file_name": file.filename,
        "file_size": len(content),
    }

    return {
        "session_id": session_id,
        "file_name": file.filename,
        "file_size": len(content),
    }


@app.get("/api/tech-stacks")
async def list_tech_stacks():
    """获取所有可用的技术栈列表"""
    tech_dir = os.path.join(BASE_DIR, "data", "technology_stack")
    if not os.path.exists(tech_dir):
        return {"tech_stacks": []}
    files = sorted([f.replace(".txt", "") for f in os.listdir(tech_dir) if f.endswith(".txt")])
    return {"tech_stacks": files}


@app.get("/api/download/{file_type}")
async def download_file(file_type: str):
    """下载生成的文件"""
    file_map = {
        "pdf": "Optimized_Resume.pdf",
        "markdown": "optimized_resume.md",
        "self_intro": "self_introduction.md",
        "interview": "interview_questions.md",
        "summary": "optimization_summary.md",
    }

    if file_type not in file_map:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_type}")

    file_path = os.path.join(OUTPUT_DIR, file_map[file_type])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件未生成，请先执行优化")

    return FileResponse(
        file_path,
        filename=file_map[file_type],
        media_type="application/octet-stream",
    )


@app.get("/api/memory")
async def list_memory():
    """查看所有缓存条目"""
    from src.conf import MEMORY_DIR
    if not os.path.exists(MEMORY_DIR):
        return {"entries": []}

    entries = []
    for f in os.listdir(MEMORY_DIR):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(MEMORY_DIR, f), "r", encoding="utf-8") as fp:
                data = json.load(fp)
                entries.append({
                    "file": f,
                    "section_key": data.get("section_key", ""),
                    "hash": data.get("hash", "")[:12],
                    "context": data.get("context", {}),
                })
        except Exception:
            pass

    return {"entries": entries, "total": len(entries)}


@app.delete("/api/memory/{section_key}")
async def clear_memory(section_key: str):
    """清理指定模块的缓存"""
    memory_manager.clear_memory(section_key if section_key != "all" else None)
    return {"message": f"已清理 [{section_key}] 缓存"}


# ─── WebSocket 实时优化 ────────────────────────────────────

@app.websocket("/ws/optimize/{session_id}")
async def optimize_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket 端点 — 实时推送 Agent 执行进度

    客户端发送: {"job_name": "Python开发工程师", "job_age": "3年"}
    服务端推送:
        {"type": "status", "message": "..."}
        {"type": "agent_start", "agent": "extractor"}
        {"type": "agent_done", "agent": "title", "content": "..."}
        {"type": "memory_hit", "agent": "skills"}
        {"type": "progress", "current": 3, "total": 12, "message": "..."}
        {"type": "complete", "outputs": {...}, "sections": {...}}
        {"type": "error", "message": "..."}
    """
    await websocket.accept()

    if session_id not in sessions:
        await websocket.send_json({"type": "error", "message": "会话不存在，请先上传简历"})
        await websocket.close()
        return

    # 检查 API Key
    if not any(os.getenv(k) for k in ["DASHSCOPE_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ZHIPU_API_KEY"]):
        await websocket.send_json({"type": "error", "message": "未配置 API Key，请在 .env 文件中配置"})
        await websocket.close()
        return

    try:
        # 接收参数
        params = await websocket.receive_json()
        job_name = params.get("job_name", "Python开发工程师")
        job_age = params.get("job_age", "3年")

        session = sessions[session_id]

        # 加载技术栈
        await websocket.send_json({"type": "status", "message": "正在匹配技术栈..."})
        tech_stack_dir = os.path.join(BASE_DIR, "data", "technology_stack")
        tech_file = route_job_to_tech_stack(job_name, tech_stack_dir)
        tech_stack = read_tech_stack_tool.invoke(os.path.join(tech_stack_dir, tech_file))

        if tech_stack.startswith("Error"):
            await websocket.send_json({"type": "error", "message": tech_stack})
            await websocket.close()
            return

        await websocket.send_json({"type": "status", "message": f"已加载技术栈: {os.path.basename(tech_file)}"})

        # 初始化状态
        initial_state = {
            "resume_path": session["resume_path"],
            "job_name": job_name,
            "job_age": job_age,
            "technology_stack": tech_stack,
            "work_dir": BASE_DIR,
            "original_resume_text": "",
            "optimized_resume_text": "",
            "sections": {},
            "progress": [],
            "logs": [],
        }

        # 定义 Agent 列表（与 graph.py 中的节点顺序一致）
        AGENT_LIST = [
            "extractor", "title", "personal_info", "skills", "certificate",
            "work_experience", "education", "project_experience", "self_evaluation",
            "assembler", "layout_expert", "interviewer"
        ]
        total = len(AGENT_LIST)

        # 使用 asyncio.Queue 在线程和协程之间传递事件
        event_queue: asyncio.Queue = asyncio.Queue()

        def run_graph_sync():
            """在线程中同步执行 LangGraph 工作流"""
            graph = create_graph()
            current_state = initial_state.copy()
            last_progress_count = 0

            for event in graph.stream(initial_state):
                for node_name, node_state in event.items():
                    current_state.update(node_state)

                    # 检查 memory_hits 增量
                    memory_hits = node_state.get("memory_hits", [])
                    if memory_hits and len(memory_hits) > len(current_state.get("memory_hits", [])[:len(memory_hits)]):
                        # 有新的 memory hit
                        pass

                    # 检查 progress 增量
                    progress_list = node_state.get("progress", [])
                    if progress_list and len(progress_list) > last_progress_count:
                        new_progress = progress_list[last_progress_count:]
                        last_progress_count = len(progress_list)
                        for p in new_progress:
                            event_queue.put_nowait({
                                "type": "progress",
                                "agent": node_name,
                                "message": p,
                            })

                    # 计算进度
                    idx = AGENT_LIST.index(node_name) if node_name in AGENT_LIST else 0
                    event_queue.put_nowait({
                        "type": "agent_done",
                        "agent": node_name,
                        "current": idx + 1,
                        "total": total,
                        "content": str(node_state.get("sections", {}).get(node_name, ""))[:200],
                    })

            return current_state

        await websocket.send_json({"type": "status", "message": "工作流初始化完成，开始执行..."})

        # 在线程池中执行图
        loop = asyncio.get_event_loop()
        graph_task = loop.run_in_executor(None, run_graph_sync)

        # 同时消费事件队列并发送给客户端
        final_state = None
        graph_completed = False

        async def send_events():
            nonlocal final_state, graph_completed
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.5)
                    await websocket.send_json(event)
                except asyncio.TimeoutError:
                    # 检查图是否完成
                    if graph_completed:
                        break
                    continue

        # 启动事件发送协程
        send_task = asyncio.create_task(send_events())

        # 等待图执行完成
        final_state = await graph_task
        graph_completed = True

        # 等待发送任务完成
        await asyncio.sleep(0.5)
        send_task.cancel()
        try:
            await send_task
        except asyncio.CancelledError:
            pass

        # 发送完成事件
        sections = final_state.get("sections", {})
        memory_hits = final_state.get("memory_hits", [])

        await websocket.send_json({
            "type": "complete",
            "outputs": {
                "pdf": "/api/download/pdf",
                "markdown": "/api/download/markdown",
                "self_intro": "/api/download/self_intro",
                "interview": "/api/download/interview",
                "summary": "/api/download/summary",
            },
            "sections": {k: v[:300] for k, v in sections.items()},  # 预览前300字
            "memory_hits": memory_hits,
        })

    except WebSocketDisconnect:
        print(f"[WebSocket] 客户端断开连接: {session_id}")
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": f"执行出错: {str(e)}"})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ─── 静态文件（生产模式） ──────────────────────────────────

# 如果 web/dist 目录存在，则直接托管前端静态文件
dist_dir = os.path.join(BASE_DIR, "web", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 AI 简历优化系统 Web UI")
    print("   后端 API: http://localhost:8000")
    print("   API 文档: http://localhost:8000/docs")
    print("   前端开发: http://localhost:5173 (需另起终端)\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
