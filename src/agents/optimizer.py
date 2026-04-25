import os
from src.state import AgentState
from src.llm.factory import get_llm
from src.prompts.optimizer_prompt import RESUME_OPTIMIZE_PROMPT, OPTIMIZATION_SUMMARY_PROMPT
from src.tools.file_ops import save_document_tool, generate_docx_tool
from src.tools.pdf_ops import generate_pdf_tool
from rich.console import Console

console = Console()

def optimizer_agent(state: AgentState):
    """
    Agent responsible for optimizing the resume and generating summary.
    """
    logs = []
    llm = get_llm()
    
    console.print("[bold blue]【优化智能体】 正在调用【LLM工厂】完成工作：初始化模型...[/bold blue]")
    logs.append("【优化智能体】 初始化模型完成。")
    
    # 1. Optimize Resume
    console.print("[cyan]【优化智能体】 正在调用【LLM】完成工作：优化简历内容（这可能需要一些时间）...[/cyan]")
    logs.append("【优化智能体】 开始优化简历...")
    
    try:
        optimize_prompt = RESUME_OPTIMIZE_PROMPT.format(
            job_name=state["job_name"],
            job_age=state["job_age"],
            technology_stack=state["technology_stack"],
            resume_content=state["original_resume_text"]
        )
        
        optimized_response = llm.invoke(optimize_prompt)
        optimized_text = optimized_response.content
        logs.append("【优化智能体】 完成【简历优化】工作。")
        console.print("[green]【优化智能体】 完成【简历优化】工作。[/green]")
    except Exception as e:
        error_msg = f"【优化智能体】 错误：优化简历失败 - {str(e)}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logs.append(error_msg)
        return {"logs": logs}
    
    # 2. Generate Summary
    console.print("[cyan]【优化智能体】 正在调用【LLM】完成工作：生成优化总结...[/cyan]")
    logs.append("【优化智能体】 开始生成总结...")
    
    try:
        summary_prompt = OPTIMIZATION_SUMMARY_PROMPT.format(
            original_resume=state["original_resume_text"],
            optimized_resume=optimized_text,
            job_name=state["job_name"]
        )
        
        summary_response = llm.invoke(summary_prompt)
        summary_text = summary_response.content
        logs.append("【优化智能体】 完成【总结生成】工作。")
        console.print("[green]【优化智能体】 完成【总结生成】工作。[/green]")
    except Exception as e:
        error_msg = f"【优化智能体】 错误：生成总结失败 - {str(e)}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logs.append(error_msg)
        summary_text = "Error generating summary."
    
    # 3. Save Files
    out_dir = os.path.join(state["work_dir"], "Optimized_Output")
    
    msg_save = f"【优化智能体】 正在调用【保存工具】完成工作：保存总结到 {out_dir}..."
    console.print(f"[cyan]{msg_save}[/cyan]")
    logs.append(msg_save)
    
    # Save intermediate optimized resume (optional, for reference)
    save_document_tool.invoke({"content": optimized_text, "file_path": os.path.join(out_dir, "optimized_resume_intermediate.md")})
    # Save summary
    save_document_tool.invoke({"content": summary_text, "file_path": os.path.join(out_dir, "optimization_summary.md")})
    
    # Note: Final PDF/DOCX generation is now handled by the structure_optimizer agent
    
    return {
        "optimized_resume_text": optimized_text,
        "optimization_summary": summary_text,
        "progress": ["Resume Optimized", "Summary Generated"],
        "logs": logs
    }
