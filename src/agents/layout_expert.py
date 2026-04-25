import os
from src.state import AgentState
from src.tools.file_ops import generate_docx_tool
from src.tools.pdf_ops import generate_pdf_tool
from rich.console import Console

console = Console()

def layout_expert_agent(state: AgentState):
    """
    Agent responsible for Rendering the final resume document (PDF/DOCX).
    It takes the structured markdown and applies visual styling.
    """
    logs = []
    console.print("[cyan]【排版渲染智能体】 正在生成最终简历文件...[/cyan]")
    logs.append("【排版渲染智能体】 开始生成文件...")
    
    current_resume = state.get("optimized_resume_text", "")
    if not current_resume:
        msg = "【排版渲染智能体】 错误：未找到结构化的简历内容。"
        console.print(f"[bold red]{msg}[/bold red]")
        logs.append(msg)
        return {"logs": logs}

    out_dir = os.path.join(state["work_dir"], "Optimized_Output")
    input_ext = state.get("resume_file_extension", ".pdf").lower()
    progress_msg = ""
    
    try:
        if input_ext == ".docx":
            # Generate Word
            docx_path = os.path.join(out_dir, "Optimized_Resume.docx")
            msg_doc = f"【排版渲染智能体】 检测到输入为Word，正在生成Word文档 {docx_path}..."
            console.print(f"[cyan]{msg_doc}[/cyan]")
            logs.append(msg_doc)
            doc_result = generate_docx_tool.invoke({"markdown_content": current_resume, "output_path": docx_path})
            logs.append(f"【排版渲染智能体】 {doc_result}")
            progress_msg = "Word Document Created"
        else:
            # Generate PDF (Default)
            pdf_path = os.path.join(out_dir, "Optimized_Resume.pdf")
            msg_pdf = f"【排版渲染智能体】 检测到输入为PDF(或默认)，正在生成PDF {pdf_path}..."
            console.print(f"[cyan]{msg_pdf}[/cyan]")
            logs.append(msg_pdf)
            pdf_result = generate_pdf_tool.invoke({"markdown_content": current_resume, "output_path": pdf_path})
            logs.append(f"【排版渲染智能体】 {pdf_result}")
            progress_msg = "PDF Created"
            
        logs.append("【排版渲染智能体】 文件生成完成。")
        console.print("[green]【排版渲染智能体】 文件生成完成。[/green]")
        
        return {
            "progress": ["Layout Rendered", progress_msg],
            "logs": logs
        }

    except Exception as e:
        error_msg = f"【排版渲染智能体】 错误：文件生成失败 - {str(e)}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logs.append(error_msg)
        return {"logs": logs}
