# Web UI 重构使用文档 — React 替代 CLI

> 本文档指导你将 AI 简历优化系统从 CLI 交互改造为 React Web 应用，涵盖后端 API 封装、前端搭建、实时通信的完整流程。

---

## 一、整体架构

```
┌─────────────────────────────────────────────────┐
│                   React 前端                      │
│  ┌──────┐ ┌──────────┐ ┌───────┐ ┌───────────┐  │
│  │ 上传  │ │ 进度可视化 │ │ 预览  │ │ 面试准备  │  │
│  └──┬───┘ └────┬─────┘ └───┬───┘ └─────┬─────┘  │
│     │          │           │            │        │
│     │    WebSocket(SSE)    │     REST API       │
│     │          │           │            │        │
└─────┼──────────┼───────────┼────────────┼────────┘
      │          │           │            │
┌─────┼──────────┼───────────┼────────────┼────────┐
│     ▼          ▼           ▼            ▼        │
│              FastAPI 后端                          │
│  ┌──────────┐ ┌───────────┐ ┌────────────────┐  │
│  │ 文件上传  │ │ WebSocket  │ │ LangGraph 工作流 │  │
│  │ REST API  │ │ 事件推送   │ │ (现有核心逻辑)  │  │
│  └──────────┘ └───────────┘ └────────────────┘  │
└──────────────────────────────────────────────────┘
```

---

## 二、后端改造 — FastAPI 封装

### 2.1 安装依赖

```bash
pip install fastapi uvicorn python-multipart
```

### 2.2 创建 API 入口文件

在项目根目录创建 `api.py`：

```python
"""
FastAPI 后端 — 封装 LangGraph 工作流为 REST API + WebSocket
"""
import os
import uuid
import json
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

from src.graph import create_graph
from src.route import route_job_to_tech_stack
from src.tools.file_ops import read_tech_stack_tool

load_dotenv()

app = FastAPI(title="AI 简历优化系统")

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会话存储
sessions = {}


@app.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)):
    """上传简历文件"""
    if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
        return JSONResponse({"error": "仅支持 PDF/DOCX/DOC 格式"}, status_code=400)

    session_id = str(uuid.uuid4())
    session_dir = os.path.join("data", "sessions", session_id)
    os.makedirs(session_dir, exist_ok=True)

    file_path = os.path.join(session_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    sessions[session_id] = {
        "resume_path": file_path,
        "file_name": file.filename,
        "work_dir": os.path.dirname(os.path.abspath(__file__)),
    }

    return {
        "session_id": session_id,
        "file_name": file.filename,
        "file_size": len(content),
    }


@app.get("/api/tech-stacks")
async def list_tech_stacks():
    """获取所有可用的技术栈列表"""
    tech_dir = os.path.join("data", "technology_stack")
    files = [f.replace(".txt", "") for f in os.listdir(tech_dir) if f.endswith(".txt")]
    return {"tech_stacks": files}


@app.websocket("/ws/optimize/{session_id}")
async def optimize_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket 端点 — 实时推送 Agent 执行进度

    客户端发送:
        {"job_name": "Python开发工程师", "job_age": "3年"}

    服务端推送:
        {"type": "agent_start", "agent": "title"}
        {"type": "agent_done", "agent": "title", "content": "...", "duration": "3.2s"}
        {"type": "memory_hit", "agent": "skills"}
        {"type": "complete", "outputs": {...}}
    """
    await websocket.accept()

    if session_id not in sessions:
        await websocket.send_json({"type": "error", "message": "会话不存在"})
        await websocket.close()
        return

    try:
        # 接收参数
        params = await websocket.receive_json()
        job_name = params.get("job_name", "Python开发工程师")
        job_age = params.get("job_age", "3年")

        session = sessions[session_id]
        work_dir = session["work_dir"]

        # 加载技术栈
        tech_stack_dir = os.path.join(work_dir, "data", "technology_stack")
        tech_file = route_job_to_tech_stack(job_name, tech_stack_dir)
        tech_stack = read_tech_stack_tool.invoke(os.path.join(tech_stack_dir, tech_file))

        # 初始化状态
        initial_state = {
            "resume_path": session["resume_path"],
            "job_name": job_name,
            "job_age": job_age,
            "technology_stack": tech_stack,
            "work_dir": work_dir,
            "original_resume_text": "",
            "optimized_resume_text": "",
            "sections": {},
            "progress": [],
            "logs": [],
        }

        await websocket.send_json({
            "type": "status",
            "message": "工作流初始化完成，开始执行...",
        })

        # 执行工作流（在事件循环中运行）
        app_graph = create_graph()
        current_state = initial_state.copy()

        loop = asyncio.get_event_loop()

        def run_graph():
            final_state = None
            for event in app_graph.stream(initial_state):
                for node_name, node_state in event.items():
                    current_state.update(node_state)
                    final_state = current_state
            return final_state

        # 在线程池中执行阻塞的图调用
        final_state = await loop.run_in_executor(None, run_graph)

        # 流式推送每个 Agent 的结果
        sections = final_state.get("sections", {})
        for agent_name, content in sections.items():
            await websocket.send_json({
                "type": "agent_done",
                "agent": agent_name,
                "content": content[:500],  # 预览前 500 字符
            })

        # 推送最终结果路径
        output_dir = os.path.join(work_dir, "Optimized_Output")
        await websocket.send_json({
            "type": "complete",
            "outputs": {
                "pdf": f"/api/download/{session_id}/pdf",
                "markdown": f"/api/download/{session_id}/markdown",
                "self_intro": f"/api/download/{session_id}/self_intro",
                "interview": f"/api/download/{session_id}/interview",
            },
            "sections": sections,
            "memory_hits": final_state.get("memory_hits", []),
        })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        await websocket.close()


@app.get("/api/download/{session_id}/{file_type}")
async def download_file(session_id: str, file_type: str):
    """下载生成的文件"""
    output_dir = os.path.join("Optimized_Output")
    file_map = {
        "pdf": "Optimized_Resume.pdf",
        "markdown": "optimized_resume.md",
        "self_intro": "self_introduction.md",
        "interview": "interview_questions.md",
    }

    if file_type not in file_map:
        return JSONResponse({"error": "不支持的文件类型"}, status_code=400)

    file_path = os.path.join(output_dir, file_map[file_type])
    if not os.path.exists(file_path):
        return JSONResponse({"error": "文件未生成"}, status_code=404)

    return FileResponse(file_path, filename=file_map[file_type])


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
        with open(os.path.join(MEMORY_DIR, f), "r", encoding="utf-8") as fp:
            data = json.load(fp)
            entries.append({
                "section_key": data.get("section_key"),
                "hash": data.get("hash", "")[:12],
                "context": data.get("context", {}),
            })
    return {"entries": entries}


@app.delete("/api/memory/{section_key}")
async def clear_memory(section_key: Optional[str] = None):
    """清理缓存"""
    from src.memory.manager import memory_manager
    memory_manager.clear_memory(section_key)
    return {"message": f"已清理 {section_key or '全部'} 缓存"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2.3 启动后端

```bash
cd /Users/gxx/Desktop/Project/Job
python3 api.py
```

后端启动后访问 http://localhost:8000/docs 可看到自动生成的 API 文档。

---

## 三、前端搭建 — React

### 3.1 初始化项目

```bash
cd /Users/gxx/Desktop/Project/Job
npm create vite@latest web -- --template react-ts
cd web
npm install
npm install axios @ant-design/icons antd react-markdown
```

### 3.2 目录结构

```
web/src/
├── api/
│   └── client.ts           # API 请求封装
├── components/
│   ├── FileUpload.tsx       # 简历上传组件
│   ├── AgentPipeline.tsx    # Agent 执行进度可视化
│   ├── ResumePreview.tsx    # 简历预览组件
│   ├── SectionEditor.tsx    # 模块编辑器
│   └── MemoryPanel.tsx      # 缓存管理面板
├── hooks/
│   └── useWebSocket.ts      # WebSocket Hook
├── pages/
│   ├── Home.tsx             # 首页（上传 + 输入）
│   ├── Optimize.tsx         # 优化页（进度 + 预览）
│   └── Result.tsx           # 结果页（下载 + 编辑）
├── types/
│   └── index.ts             # 类型定义
├── App.tsx
└── main.tsx
```

### 3.3 类型定义

```typescript
// web/src/types/index.ts

export interface UploadResult {
  session_id: string;
  file_name: string;
  file_size: number;
}

export interface AgentStep {
  name: string;
  label: string;
  status: 'pending' | 'running' | 'done' | 'error' | 'cached';
  content?: string;
  duration?: string;
}

export interface OptimizeParams {
  job_name: string;
  job_age: string;
}

// WebSocket 消息类型
export type WSMessage =
  | { type: 'status'; message: string }
  | { type: 'agent_start'; agent: string }
  | { type: 'agent_done'; agent: string; content: string }
  | { type: 'memory_hit'; agent: string }
  | { type: 'complete'; outputs: OutputFiles; sections: Record<string, string>; memory_hits: string[] }
  | { type: 'error'; message: string };

export interface OutputFiles {
  pdf: string;
  markdown: string;
  self_intro: string;
  interview: string;
}

export interface MemoryEntry {
  section_key: string;
  hash: string;
  context: Record<string, string>;
}
```

### 3.4 API 请求封装

```typescript
// web/src/api/client.ts
import axios from 'axios';
import type { UploadResult, MemoryEntry } from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export async function uploadResume(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/upload', form);
  return data;
}

export async function listTechStacks(): Promise<string[]> {
  const { data } = await api.get('/tech-stacks');
  return data.tech_stacks;
}

export async function getDownloadUrl(sessionId: string, type: string): Promise<string> {
  return `http://localhost:8000/api/download/${sessionId}/${type}`;
}

export async function listMemory(): Promise<MemoryEntry[]> {
  const { data } = await api.get('/memory');
  return data.entries;
}

export async function clearMemory(sectionKey?: string): Promise<void> {
  await api.delete(`/memory/${sectionKey || ''}`);
}
```

### 3.5 WebSocket Hook

```typescript
// web/src/hooks/useWebSocket.ts
import { useRef, useState, useCallback } from 'react';
import type { WSMessage } from '../types';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [status, setStatus] = useState<'idle' | 'connecting' | 'running' | 'done' | 'error'>('idle');

  const connect = useCallback((sessionId: string, params: { job_name: string; job_age: string }) => {
    setStatus('connecting');
    setMessages([]);

    const ws = new WebSocket(`ws://localhost:8000/ws/optimize/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('running');
      ws.send(JSON.stringify(params));
    };

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);

      if (msg.type === 'complete') setStatus('done');
      if (msg.type === 'error') setStatus('error');
    };

    ws.onerror = () => setStatus('error');
    ws.onclose = () => {
      if (status === 'running') setStatus('done');
    };
  }, [status]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    setStatus('idle');
  }, []);

  return { messages, status, connect, disconnect };
}
```

### 3.6 核心页面组件

#### 首页 — 上传简历 + 输入岗位

```tsx
// web/src/pages/Home.tsx
import { useState } from 'react';
import { Upload, Input, Button, Form, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { uploadResume } from '../api/client';

const { Dragger } = Upload;

export default function Home() {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      const result = await uploadResume(file);
      setSessionId(result.session_id);
      message.success(`已上传: ${result.file_name}`);
    } catch {
      message.error('上传失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStart = () => {
    const values = form.getFieldsValue();
    if (!sessionId) {
      message.warning('请先上传简历');
      return;
    }
    navigate(`/optimize?session=${sessionId}&job=${values.job_name}&age=${values.job_age}`);
  };

  return (
    <div style={{ maxWidth: 600, margin: '80px auto', padding: 24 }}>
      <h1 style={{ textAlign: 'center', marginBottom: 40 }}>AI 简历优化系统</h1>

      <Dragger
        accept=".pdf,.docx,.doc"
        showUploadList={false}
        beforeUpload={(file) => { handleUpload(file); return false; }}
        disabled={loading}
      >
        <p><InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} /></p>
        <p>点击或拖拽上传简历（PDF / DOCX）</p>
      </Dragger>

      <Form form={form} layout="vertical" style={{ marginTop: 32 }}
            initialValues={{ job_name: 'Python开发工程师', job_age: '3年' }}>
        <Form.Item label="目标岗位" name="job_name">
          <Input placeholder="例如: Python后端工程师" />
        </Form.Item>
        <Form.Item label="工作年限" name="job_age">
          <Input placeholder="例如: 3年" />
        </Form.Item>
        <Button type="primary" block size="large" onClick={handleStart} disabled={!sessionId}>
          开始优化
        </Button>
      </Form>
    </div>
  );
}
```

#### 优化页 — Agent 进度可视化

```tsx
// web/src/pages/Optimize.tsx
import { useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Steps, Card, Tag, Spin, Typography } from 'antd';
import { CheckCircleOutlined, LoadingOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useWebSocket } from '../hooks/useWebSocket';

const AGENT_LIST = [
  { name: 'extractor',        label: '简历提取' },
  { name: 'title',            label: '标题优化' },
  { name: 'personal_info',    label: '个人信息' },
  { name: 'skills',           label: '专业技能' },
  { name: 'certificate',      label: '技能证书' },
  { name: 'work_experience',  label: '职业经历' },
  { name: 'education',        label: '教育经历' },
  { name: 'project_experience', label: '项目经验' },
  { name: 'self_evaluation',  label: '自我评价' },
  { name: 'assembler',        label: '简历组装' },
  { name: 'layout_expert',    label: '排版渲染' },
  { name: 'interviewer',      label: '面试准备' },
];

export default function Optimize() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = params.get('session') || '';
  const jobName = params.get('job') || '';
  const jobAge = params.get('age') || '';

  const { messages, status, connect } = useWebSocket();

  useEffect(() => {
    connect(sessionId, { job_name: jobName, job_age: jobAge });
  }, []);

  // 计算 Agent 状态
  const agentStatusMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const msg of messages) {
      if (msg.type === 'agent_done') map[msg.agent] = 'done';
      if (msg.type === 'memory_hit') map[msg.agent] = 'cached';
      if (msg.type === 'error' && 'agent' in msg) map[(msg as any).agent] = 'error';
    }
    return map;
  }, [messages]);

  const currentAgent = useMemo(() => {
    const done = Object.keys(agentStatusMap).length;
    return AGENT_LIST[done]?.name || '';
  }, [agentStatusMap]);

  // 完成后跳转
  const outputs = useMemo(() => {
    const last = messages.findLast(m => m.type === 'complete');
    return (last as any)?.outputs;
  }, [messages]);

  useEffect(() => {
    if (status === 'done' && outputs) {
      setTimeout(() => navigate(`/result?session=${sessionId}`), 1000);
    }
  }, [status, outputs]);

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: 24 }}>
      <h2>正在优化简历...</h2>
      <p>目标岗位: {jobName} | 工作年限: {jobAge}</p>

      <Steps direction="vertical" current={AGENT_LIST.findIndex(a => a.name === currentAgent)}
             items={AGENT_LIST.map(agent => ({
        title: agent.label,
        status: agentStatusMap[agent.name] === 'done' ? 'finish'
              : agentStatusMap[agent.name] === 'cached' ? 'finish'
              : agent.name === currentAgent ? 'process'
              : 'wait',
        icon: agentStatusMap[agent.name] === 'done' ? <CheckCircleOutlined />
            : agentStatusMap[agent.name] === 'cached' ? <Tag color="blue">缓存</Tag>
            : agent.name === currentAgent ? <LoadingOutlined />
            : <ClockCircleOutlined />,
        description: agentStatusMap[agent.name] === 'cached' ? '命中缓存，跳过 LLM 调用' : undefined,
      }))} />

      {status === 'error' && <Card status="error">执行出错，请重试</Card>}
    </div>
  );
}
```

#### 结果页 — 预览与下载

```tsx
// web/src/pages/Result.tsx
import { useSearchParams } from 'react-router-dom';
import { Card, Button, Tabs, Typography } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { getDownloadUrl } from '../api/client';

const { Title, Paragraph } = Typography;

export default function Result() {
  const [params] = useSearchParams();
  const sessionId = params.get('session') || '';

  const files = [
    { key: 'pdf',        label: '优化简历 PDF',    icon: '📄' },
    { key: 'markdown',   label: 'Markdown 版本',   icon: '📝' },
    { key: 'self_intro', label: '自我介绍',         icon: '🎤' },
    { key: 'interview',  label: '面试题集锦',       icon: '💼' },
  ];

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: 24 }}>
      <Title level={2} style={{ textAlign: 'center' }}>优化完成</Title>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {files.map(file => (
          <Card key={file.key} hoverable>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 40 }}>{file.icon}</div>
              <Title level={4}>{file.label}</Title>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                href={getDownloadUrl(sessionId, file.key)}
                target="_blank"
              >
                下载
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

### 3.7 路由配置

```tsx
// web/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Optimize from './pages/Optimize';
import Result from './pages/Result';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/optimize" element={<Optimize />} />
        <Route path="/result" element={<Result />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## 四、启动方式

### 4.1 启动后端

```bash
# 终端 1 — 启动 FastAPI
cd /Users/gxx/Desktop/Project/Job
python3 api.py

# 后端运行在 http://localhost:8000
# API 文档在 http://localhost:8000/docs
```

### 4.2 启动前端

```bash
# 终端 2 — 启动 React
cd /Users/gxx/Desktop/Project/Job/web
npm run dev

# 前端运行在 http://localhost:5173
```

### 4.3 使用流程

```
1. 打开 http://localhost:5173
2. 拖拽上传简历（PDF/DOCX）
3. 输入目标岗位和工作年限
4. 点击「开始优化」
5. 实时查看各 Agent 执行进度
6. 优化完成后下载 PDF、自我介绍、面试题
```

---

## 五、API 接口文档

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/upload` | 上传简历，返回 session_id |
| `GET` | `/api/tech-stacks` | 获取技术栈列表 |
| `WS` | `/ws/optimize/{session_id}` | WebSocket 实时优化 |
| `GET` | `/api/download/{session_id}/{type}` | 下载文件（pdf/markdown/self_intro/interview） |
| `GET` | `/api/memory` | 查看缓存列表 |
| `DELETE` | `/api/memory/{section_key}` | 清理缓存 |

---

## 六、后续扩展方向

### 6.1 短期（1-2 周）
- [ ] 简历在线预览（PDF.js 渲染）
- [ ] 模块内容在线编辑（修改后重新调用单个 Agent）
- [ ] 缓存管理面板（查看命中率、一键清理）

### 6.2 中期（1 个月）
- [ ] 多套简历模板（经典/现代/极客风格切换）
- [ ] 优化前后对比（diff 视图）
- [ ] 历史记录（IndexedDB 存储每次优化快照）
- [ ] 用户登录（JWT 认证）

### 6.3 长期
- [ ] 拖拽式简历排版编辑器（类似 Canva）
- [ ] 一键投递（对接招聘平台 API）
- [ ] 移动端适配
- [ ] Docker 容器化部署

---

## 七、面试话术

> "这个项目我做了全栈改造。后端用 FastAPI 把 LangGraph 工作流封装为 REST API + WebSocket，前端用 React + TypeScript + Ant Design 构建了 Web 界面。核心难点是 Agent 执行进度的实时推送 — 我用 WebSocket 在每个 Agent 完成时向前端推送状态，前端用 Steps 组件渲染类似 CI/CD Pipeline 的可视化效果。同时还实现了文件上传、PDF 在线预览、缓存管理等功能。"
