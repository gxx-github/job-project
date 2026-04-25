# AI 简历优化项目讲解

## 1. 项目背景与自我介绍
> "面试官您好，我介绍一下我开发的这个‘多智能体简历优化与面试辅助系统’。这是一个基于 **LangGraph** 和 **LangChain** 框架构建的垂直领域 Agent 应用。
> 它的核心目标是解决求职者在简历撰写中‘不会挖掘亮点’和‘排版耗时’的痛点。不同于市面上简单的‘润色工具’，我设计了一套**多智能体流水线**，不仅能根据目标岗位（JD）深度重构简历内容，还能自动生成排版好的 PDF，并提供针对性的面试题和自我介绍，实现‘简历-面试’的全流程辅助。"

## 2. 技术选型与架构设计

### 2.1 核心技术栈
- **框架**: **LangGraph** (编排复杂工作流), **LangChain** (底层组件)。
- **模型**: 支持接入 DeepSeek-V3, Qwen-Max 等国产大模型，通过 OpenAI SDK 统一封装。
- **协议**: 采用 **MCP (Model Context Protocol)** 思想设计工具层，实现文件操作、PDF 生成等能力的标准化调用。
- **持久化**: 本地文件系统 + JSON 实现轻量级向量化记忆（Memory）。

### 2.2 为什么选择 LangGraph？
"在项目初期，我尝试过使用简单的 LangChain Chain 结构，但很快遇到了瓶颈：
1.  **流程非线性**: 简历优化不是一条直线，需要引入‘动态修改’（Human-in-the-loop）环节，允许用户在生成 PDF 前进行干预，这需要图（Graph）结构的循环能力。
2.  **状态管理复杂**: 需要在多个 Agent 之间传递原始简历、优化后片段、技术栈配置等大量上下文，LangGraph 的 `AgentState` 提供了非常清晰的全局状态管理。
3.  **细粒度控制**: 我需要对每个 Section（如项目经历、技能）进行独立的优化和重试控制，Graph 结构让这种模块化变得容易。"

### 2.3 系统架构详解
系统采用了 **Pipeline 模式** 的状态图，主要包含以下几个阶段：

1.  **Input & Extraction (输入与提取)**:
    - `Extractor Agent` 自动扫描并解析 PDF/Word/Markdown 格式简历，利用 OCR 或文本提取库获取 Raw Text。
    - *亮点*: 引入了条件边（Conditional Edge），如果提取失败直接终止或重试。

2.  **Section-Based Optimization (分块深度优化)**:
    - 这是一个核心设计。我没有把整份简历丢给 LLM，而是设计了 8 个专用的 **Section Agents** (`Title`, `Skills`, `Project`, `WorkExp` 等)。
    - **优势**:
        - **解决 Context Window 限制**: 避免长简历导致模型“遗忘”或注意力分散。
        - **专业度提升**: 每个 Agent 拥有独立的 System Prompt。例如，`Project Agent` 专注于 STAR 法则重构，而 `Skills Agent` 专注于去重和关键词匹配。

3.  **Memory Augmentation (记忆增强)**:
    - 为了降低 Token 消耗和提升响应速度，我实现了一个基于 **Content Hash** 的记忆模块。
    - 在每个 Section Agent 执行前，会计算 `Hash(原始文本 + 目标岗位 + 技术栈)`。如果命中缓存，直接跳过 LLM 调用。这对于调试和微调场景非常有用。

4.  **Assembly & Layout (组装与排版)**:
    - `Assembler Agent` 将各模块拼接。
    - `Layout Expert` 调用 `pdf_generator` 工具，将 Markdown 渲染为包含 CSS 样式的 PDF。这里我解决了很多中文乱码和排版错位的问题。

5.  **Dynamic Interaction (动态交互)**:
    - 利用 LangGraph 的中断机制，系统在生成 PDF 后会暂停，询问用户是否满意。如果不满意，用户可以输入自然语言指令，系统跳转回优化节点进行修改。

6.  **Interview Prep (面试辅助)**:
    - 最后，`Interviewer Agent` 读取最终定稿的简历，生成 300 字自我介绍和 8-10 道深度面试题（含参考答案）。

## 3. 关键技术难点与解决方案

### 3.1 难点一：LLM 输出格式不可控
**问题**: Agent 经常会在 JSON 中夹杂 Markdown 符号，或者生成的简历格式错乱。
**解决**:
- **Prompt 强化**: 在 System Prompt 中严格约束输出格式（如 "Only output raw JSON"）。
- **防御性编程**: 在 Tool 内部增加了 **Regex 清洗层**（`clean_text_spacing`），自动去除代码块标记、多余空格，修复 JSON 格式错误。

### 3.2 难点二：如何让优化后的简历“像人写的”？
**问题**: 早期版本生成的简历充满了“AI 味”（堆砌形容词，逻辑空洞）。
**解决**:
- **Context 注入**: 在 Prompt 中强制注入“技术栈文件”（`technology_stack.txt`），让 Agent 知道该岗位的具体关键词（如 K8s, Spring Cloud）。
- **Few-Shot Learning**: 在 Prompt 中提供优秀的简历片段作为示例（Example），引导模型模仿 STAR 原则（Situation, Task, Action, Result）。

### 3.3 难点三：PDF 中文排版与换行
**问题**: Python 的 PDF 库（如 FPDF）对中文支持不佳，经常乱码或自动换行失效。
**解决**:
- 封装了自定义的 PDF 生成工具，注册了支持中文的字体（如微软雅黑、宋体）。
- 实现了基于 Markdown 解析的渲染引擎，手动计算行宽和分页逻辑，确保生成的 PDF 专业美观。

## 4. 项目总结
"这个项目不仅是一个工具，更是我对 **Agentic Workflow** 的一次深度实践。通过将复杂任务拆解为子智能体协作，并引入记忆和人工反馈机制，我成功构建了一个高可用、低成本且结果可控的垂直领域应用。未来我计划引入 RAG 技术，让它能参考更多的优秀简历模板，进一步提升优化质量。"
