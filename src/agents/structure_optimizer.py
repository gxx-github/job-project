import os
from src.state import AgentState
from src.llm.factory import get_llm
from src.prompts.structure_prompt import STRUCTURE_OPTIMIZE_PROMPT
from src.tools.file_ops import save_document_tool
from rich.console import Console

console = Console()

def structure_optimizer_agent(state: AgentState):
    """
    Agent responsible for restructuring and cleaning the resume Markdown content ONLY.
    """
    logs = []
    llm = get_llm()
    
    console.print("[cyan]【内容结构化智能体】 正在重新组织简历内容结构...[/cyan]")
    logs.append("【内容结构化智能体】 开始重构简历结构...")
    
    # Use the optimized text if available, otherwise original
    current_resume = state.get("optimized_resume_text", "")
    if not current_resume:
        current_resume = state.get("original_resume_text", "")
        
    try:
        prompt = STRUCTURE_OPTIMIZE_PROMPT.format(
            resume_content=current_resume
        )
        
        response = llm.invoke(prompt)
        structured_resume = response.content
        
        # Simple cleanup
        if structured_resume.startswith("```markdown"):
            structured_resume = structured_resume.replace("```markdown", "", 1)
        if structured_resume.startswith("```"):
            structured_resume = structured_resume.replace("```", "", 1)
        if structured_resume.endswith("```"):
            structured_resume = structured_resume[:-3]
            
        structured_resume = structured_resume.strip()
        
        logs.append("【内容结构化智能体】 简历内容结构化完成。")
        console.print("[green]【内容结构化智能体】 简历内容结构化完成。[/green]")
        
        # Save Markdown for reference
        out_dir = os.path.join(state["work_dir"], "Optimized_Output")
        save_document_tool.invoke({"content": structured_resume, "file_path": os.path.join(out_dir, "optimized_resume.md")})

        return {
            "optimized_resume_text": structured_resume,
            "progress": ["Resume Structured"],
            "logs": logs
        }
        
    except Exception as e:
        error_msg = f"【内容结构化智能体】 错误：重构失败 - {str(e)}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logs.append(error_msg)
        return {"logs": logs}
