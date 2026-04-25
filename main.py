import os
import sys
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from src.graph import create_graph
from src.tools.file_ops import read_tech_stack_tool
from src.route import route_job_to_tech_stack
from src.memory.manager import memory_manager

console = Console()

def handle_interactive_memory(final_state):
    """
    Handle post-execution interactive memory management.
    """
    console.print("\n" + "="*50)
    console.print("[bold cyan]交互式记忆管理[/bold cyan]")
    console.print("="*50)
    
    sections = final_state.get("sections", {})
    if not sections:
        console.print("[yellow]本次运行没有产生任何优化模块，跳过记忆保存。[/yellow]")
        return

    console.print("\n本次生成的优化模块:")
    for key in sections.keys():
        console.print(f"- {key}")

    # 1. Ask user which sections to save
    console.print("\n[bold]请选择要保存到记忆库的模块[/bold]")
    console.print("输入模块名称（多个用逗号分隔，例如: title, skills），直接回车跳过")
    
    user_input = Prompt.ask("要保存的模块")
    
    if user_input.strip():
        selected_keys = [k.strip() for k in user_input.split(",") if k.strip()]
        
        # Context needed for saving
        context = {
            "job_name": final_state.get("job_name", ""),
            "technology_stack": final_state.get("technology_stack", "")
        }
        
        # Special context for self_evaluation
        if "self_evaluation" in selected_keys:
             # We need to reconstruct the summary used for hash context
             # This must match logic in section_agents.py
             summary_str = json.dumps(sections, sort_keys=True, ensure_ascii=False)
             context["sections_summary"] = summary_str

        for key in selected_keys:
            if key in sections:
                # We need original content. 
                # Note: For simplicity, we use the FULL original resume as the 'original_content' key 
                # because section agents extract from full resume.
                original_content = final_state.get("original_resume_text", "")
                optimized_content = sections[key]
                
                # Special handling: self_eval context is different (handled above if key is self_eval)
                # But wait, save_optimized_content takes a single context dict.
                # If key is self_eval, we add extra context. 
                # If key is NOT self_eval, we should NOT have sections_summary in context to match section_agents logic?
                # Let's check section_agents.py logic.
                # It uses a FRESH context dict for each call.
                
                current_context = {
                    "job_name": final_state.get("job_name", ""),
                    "technology_stack": final_state.get("technology_stack", "")
                }
                
                if key == "self_evaluation":
                     summary_str = json.dumps(sections, sort_keys=True, ensure_ascii=False)
                     current_context["sections_summary"] = summary_str
                
                # Check existence first
                existing_content = memory_manager.get_optimized_content(key, original_content, current_context)
                should_save = True
                
                if existing_content:
                     # If content is exactly the same, no need to ask
                    if existing_content == optimized_content:
                        console.print(f"[dim]模块 [{key}] 内容未变更，跳过保存。[/dim]")
                        continue
                        
                    should_save = Confirm.ask(f"[yellow]检测到模块 [{key}] 已存在历史记忆。是否覆盖更新？[/yellow]", default=True)
                
                if should_save:
                    memory_manager.save_optimized_content(key, original_content, optimized_content, current_context)
                    console.print(f"[green]模块 [{key}] 记忆已保存/更新。[/green]")
                else:
                    console.print(f"[dim]模块 [{key}] 记忆更新已取消。[/dim]")

            else:
                console.print(f"[red]未找到模块: {key}[/red]")

    # 2. Memory Maintenance (Clean/Update)
    if Confirm.ask("\n是否需要进行高级记忆维护（清理/手动更新）？"):
        from utils.interactive_memory import interactive_mode
        interactive_mode()

def main():
    # 1. Load Environment
    load_dotenv()
    work_dir = os.path.dirname(os.path.abspath(__file__))
    
    console.print(Panel.fit("[bold blue]多智能体简历优化与面试准备系统 (LangGraph Edition)[/bold blue]"))

    # 2. Check Prerequisites
    if not any(os.getenv(k) for k in ["DASHSCOPE_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ZHIPU_API_KEY"]):
        console.print("[bold red]错误: 未找到 API Key。请在 .env 文件中配置 DASHSCOPE_API_KEY / OPENAI_API_KEY / DEEPSEEK_API_KEY / ZHIPU_API_KEY[/bold red]")
        return

    # 3. User Interaction
    console.print("\n" + "="*50)
    console.print("[bold cyan]请输入关键求职信息[/bold cyan]")

    # 自动扫描简历文件
    data_dir = os.path.join(work_dir, "data")
    resume_path = None
    
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        candidates = [f for f in files if f.lower().endswith(('.pdf', '.docx', '.doc'))]
        if candidates:
            # 默认取第一个找到的简历文件
            resume_path = os.path.join(data_dir, candidates[0])
            console.print(f"[green]已自动识别简历文件: {candidates[0]}[/green]")
        else:
             console.print(f"[red]错误: 在 {data_dir} 目录下未找到有效的简历文件 (.pdf, .docx, .doc)[/red]")
             return
    else:
        console.print(f"[red]错误: 数据目录 {data_dir} 不存在[/red]")
        return

    job_name = Prompt.ask("请输入您的[bold green]目标岗位[/bold green] (例如: Python后端工程师)", default="Python开发工程师")
    job_age = Prompt.ask("请输入您的[bold green]工作年限[/bold green] (例如: 3年)", default="3年")
    console.print("="*50 + "\n")
    
    # 4. Load Tech Stack (Intelligent Routing)
    tech_stack_dir = os.path.join(work_dir, "data", "technology_stack")
    tech_file_name = route_job_to_tech_stack(job_name, tech_stack_dir)
    
    tech_stack_path = os.path.join(tech_stack_dir, tech_file_name)
    
    # Fallback to data root if not found (legacy)
    if not os.path.exists(tech_stack_path):
        tech_stack_path = os.path.join(work_dir, "data", tech_file_name)
        
    # Final fallback
    if not os.path.exists(tech_stack_path):
         tech_stack_path = os.path.join(work_dir, "data", "technology_stack.txt")

    console.print(f"[dim]加载技术栈文件: {os.path.basename(tech_stack_path)}[/dim]")
    tech_stack = read_tech_stack_tool.invoke(tech_stack_path)
    
    if tech_stack.startswith("Error"):
        console.print(f"[bold red]{tech_stack}[/bold red]")
        return
        
    console.print(f"\n[green]已加载技术栈配置:[/green] {tech_stack[:50]}...")

    # 5. Initialize Graph
    app = create_graph()
    
    # 6. Execute Workflow with Progress Bar
    initial_state = {
        "resume_path": resume_path,
        "job_name": job_name,
        "job_age": job_age,
        "technology_stack": tech_stack,
        "work_dir": work_dir,
        "original_resume_text": "",
        "optimized_resume_text": "",
        "sections": {},
        "progress": [],
        "logs": []
    }
    
    final_state = None # To store final state for post-processing

    console.print("\n[bold yellow]开始执行智能体工作流...[/bold yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        task_id = progress.add_task("系统初始化...", total=None)
        
        # Stream events from the graph
        try:
            last_log_count = 0
            # We need to capture the final state. 
            # app.stream yields partial updates. The last event contains the final update.
            # However, for memory saving, we need the COMPLETE final state.
            # app.invoke returns the final state, but doesn't stream.
            # To have both streaming and final state, we can maintain a local state merge
            # OR just use invoke if we don't care about real-time progress too much (but we do).
            # LangGraph's stream returns output of each node. We can accumulate it.
            
            # Actually, let's just use a simple variable to hold the last node's state
            current_full_state = initial_state.copy()
            
            for event in app.stream(initial_state):
                for node_name, node_state in event.items():
                    # Merge node_state into current_full_state (simplified merge)
                    current_full_state.update(node_state)
                    
                    # Update logs - Only print NEW logs
                    if "logs" in node_state and node_state["logs"]:
                        current_logs = node_state["logs"]
                        if len(current_logs) > last_log_count:
                            last_log_count = len(current_logs)
                            
                    # Update progress status
                    if "progress" in node_state and node_state["progress"]:
                        latest_update = node_state["progress"][-1]
                        progress.update(task_id, description=f"[green]智能体 [{node_name}] 完成: {latest_update}")
                    else:
                        progress.update(task_id, description=f"[cyan]正在执行: {node_name}...")
            
            final_state = current_full_state
            progress.update(task_id, completed=100, description="[bold green]所有任务执行完毕！[/bold green]")
            
        except Exception as e:
            progress.update(task_id, description=f"[bold red]执行出错: {str(e)}[/bold red]")
            console.print_exception()
            return

    # 7. Final Output (Printed ONLY once after loop)
    output_dir = os.path.join(work_dir, "Optimized_Output")
    console.print("\n[bold]生成文件清单:[/bold]")
    console.print(f"- [blue]{os.path.join(output_dir, 'optimized_resume.md')}[/blue]")
    console.print(f"- [blue]{os.path.join(output_dir, 'Optimized_Resume.pdf')}[/blue]")
    console.print(f"- [blue]{os.path.join(output_dir, 'optimization_summary.md')}[/blue]")
    console.print(f"- [blue]{os.path.join(output_dir, 'self_introduction.md')}[/blue]")
    console.print(f"- [blue]{os.path.join(output_dir, 'interview_questions.md')}[/blue]")
    
    # 8. Interactive Memory Management
    if final_state:
        handle_interactive_memory(final_state)

if __name__ == "__main__":
    main()
