import os
import time
import concurrent.futures
from rich.console import Console
from src.state import AgentState
from src.llm.factory import get_llm
from src.prompts.optimizer_prompt import SELF_INTRO_PROMPT, INTERVIEW_QUESTIONS_TEMPLATE
from src.tools.file_ops import save_document_tool
from src.conf import SELF_INTRO_LENGTH, TOTAL_INTERVIEW_QUESTIONS, QUESTIONS_PER_BATCH

console = Console()

def generate_batch(batch_config, job_name, optimized_resume, technology_stack):
    """
    Helper function to generate a single batch of questions.
    """
    llm = get_llm()
    start = batch_config["start"]
    end = batch_config["end"]
    q_type = batch_config["type"]
    
    try:
        prompt = INTERVIEW_QUESTIONS_TEMPLATE.format(
            job_name=job_name,
            optimized_resume=optimized_resume,
            technology_stack=technology_stack,
            question_type=q_type,
            num_questions=end - start + 1,
            start_index=start,
            end_index=end,
            focus_area=batch_config["focus"]
        )
        response = llm.invoke(prompt)
        return {
            "success": True,
            "start": start,
            "end": end,
            "type": q_type,
            "content": response.content
        }
    except Exception as e:
        return {
            "success": False,
            "start": start,
            "end": end,
            "error": str(e)
        }

def interviewer_agent(state: AgentState):
    """
    Agent responsible for generating self-intro and interview questions (in batches).
    """
    logs = []
    llm = get_llm()
    
    msg_start = "【面试官智能体】 正在调用【任务规划】完成工作：开始面试准备任务..."
    console.print(f"[bold blue]{msg_start}[/bold blue]")
    logs.append(msg_start)
    
    # 1. Generate Self Intro
    msg_intro = f"【面试官智能体】 正在调用【LLM】完成工作：生成自我介绍 (约{SELF_INTRO_LENGTH}字)..."
    console.print(f"[cyan]{msg_intro}[/cyan]")
    logs.append(msg_intro)
    
    try:
        intro_prompt = SELF_INTRO_PROMPT.format(
            optimized_resume=state["optimized_resume_text"],
            job_age=state["job_age"],
            technology_stack=state["technology_stack"],
            self_intro_length=SELF_INTRO_LENGTH
        )
        intro_response = llm.invoke(intro_prompt)
        intro_text = intro_response.content
        
        msg_intro_done = "【面试官智能体】 完成【自我介绍生成】工作。"
        console.print(f"[green]{msg_intro_done}[/green]")
        logs.append(msg_intro_done)
        
    except Exception as e:
        error_msg = f"【面试官智能体】 错误：生成自我介绍失败 - {str(e)}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logs.append(error_msg)
        intro_text = "Error generating self introduction."

    # 2. Generate Interview Questions (Parallel Batches)
    questions_full_text = "# 面试题集锦\n\n"
    
    # Calculate batches dynamically based on config
    total_qs = TOTAL_INTERVIEW_QUESTIONS
    per_batch = QUESTIONS_PER_BATCH
    
    # Define batch types and focus areas distribution
    # We will distribute the total questions among 4 categories roughly:
    # 10% Project, 30% Basic Skills, 30% Advanced Skills, 30% Scenario/Architecture
    
    # Helper to calculate range
    batches_config = []
    current_q = 1
    
    # 1. Project Questions (approx 10-20% or at least 1 batch)
    project_qs_count = max(per_batch, int(total_qs * 0.1))
    # Round to nearest batch size
    project_qs_count = (project_qs_count // per_batch) * per_batch
    if project_qs_count == 0: project_qs_count = per_batch
    
    for _ in range(0, project_qs_count, per_batch):
        if current_q > total_qs: break
        end_q = min(current_q + per_batch - 1, total_qs)
        batches_config.append({
            "start": current_q, 
            "end": end_q, 
            "type": "项目针对性提问", 
            "focus": "针对简历中的具体项目进行深入提问，关注技术选型理由、遇到的难点及解决方案。"
        })
        current_q = end_q + 1

    # 2. Basic Skills (approx 30%)
    basic_qs_count = int(total_qs * 0.3)
    basic_qs_count = (basic_qs_count // per_batch) * per_batch
    for _ in range(0, basic_qs_count, per_batch):
        if current_q > total_qs: break
        end_q = min(current_q + per_batch - 1, total_qs)
        batches_config.append({
            "start": current_q, 
            "end": end_q, 
            "type": "基础技能提问", 
            "focus": "编程语言基础、常用库、基本概念，考察基础知识与底层原理。"
        })
        current_q = end_q + 1

    # 3. Advanced Skills (approx 30%)
    adv_qs_count = int(total_qs * 0.3)
    adv_qs_count = (adv_qs_count // per_batch) * per_batch
    for _ in range(0, adv_qs_count, per_batch):
        if current_q > total_qs: break
        end_q = min(current_q + per_batch - 1, total_qs)
        batches_config.append({
            "start": current_q, 
            "end": end_q, 
            "type": "进阶技能提问", 
            "focus": "高级特性、工具链、最佳实践，考察进阶知识。"
        })
        current_q = end_q + 1
        
    # 4. Scenario/Market (Remaining)
    while current_q <= total_qs:
        end_q = min(current_q + per_batch - 1, total_qs)
        batches_config.append({
            "start": current_q, 
            "end": end_q, 
            "type": "场景设计与架构提问", 
            "focus": "高并发、高可用、框架原理或特定业务场景的系统设计题。"
        })
        current_q = end_q + 1

    total_batches = len(batches_config)
    msg_batch_start = f"【面试官智能体】 正在调用【并发执行】完成工作：开始生成 {total_qs} 道面试题（共 {total_batches} 批次）..."
    console.print(f"[cyan]{msg_batch_start}[/cyan]")
    logs.append(msg_batch_start)

    # Use ThreadPoolExecutor for parallel execution
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_batch = {
            executor.submit(
                generate_batch, 
                batch, 
                state["job_name"], 
                state["optimized_resume_text"], 
                state["technology_stack"]
            ): batch for batch in batches_config
        }
        
        for future in concurrent.futures.as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                data = future.result()
                results.append(data)
                if data["success"]:
                    msg_batch_done = f"【面试官智能体】 完成【批次生成】工作：Batch (Q{data['start']}-Q{data['end']}) 生成完毕。"
                    console.print(f"[green]{msg_batch_done}[/green]")
                else:
                    msg_batch_err = f"【面试官智能体】 错误：Batch (Q{batch['start']}-Q{batch['end']}) 生成失败 - {data.get('error')}"
                    console.print(f"[bold red]{msg_batch_err}[/bold red]")
                    logs.append(msg_batch_err)
            except Exception as exc:
                msg_exc = f"【面试官智能体】 错误：Batch (Q{batch['start']}-Q{batch['end']}) 异常 - {exc}"
                console.print(f"[bold red]{msg_exc}[/bold red]")
                logs.append(msg_exc)

    # Sort results by start index to assemble correctly
    results.sort(key=lambda x: x["start"])
    
    # Assemble text
    current_section = ""
    for res in results:
        if not res.get("success"):
            questions_full_text += f"\n\n**[Error generating Q{res['start']}-Q{res['end']}]**\n\n"
            continue
            
        # Add section headers
        if res["type"] != current_section:
            questions_full_text += f"## {res['type']}\n\n"
            current_section = res["type"]
            
        questions_full_text += res["content"] + "\n\n"

    msg_all_done = "【面试官智能体】 完成【面试题生成】工作：所有题目已生成。"
    console.print(f"[bold green]{msg_all_done}[/bold green]")
    logs.append(msg_all_done)
    
    # 3. Save Files
    out_dir = os.path.join(state["work_dir"], "Optimized_Output")
    
    msg_save = f"【面试官智能体】 正在调用【保存工具】完成工作：保存文件到 {out_dir}..."
    console.print(f"[cyan]{msg_save}[/cyan]")
    logs.append(msg_save)
    
    save_document_tool.invoke({"content": intro_text, "file_path": os.path.join(out_dir, "self_introduction.md")})
    save_document_tool.invoke({"content": questions_full_text, "file_path": os.path.join(out_dir, "interview_questions.md")})
    
    return {
        "self_intro": intro_text,
        "interview_questions": questions_full_text,
        "progress": ["Self Intro Generated", f"Interview Questions Generated ({total_qs} Qs)"],
        "logs": logs
    }
