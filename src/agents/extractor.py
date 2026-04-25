import os
import glob
from langchain_core.messages import HumanMessage
from src.state import AgentState
from src.tools.file_ops import read_resume_tool, save_document_tool
from rich.console import Console

console = Console()

def extractor_agent(state: AgentState):
    """
    Agent responsible for extracting text from the resume file.
    """
    work_dir = state["work_dir"]
    data_dir = os.path.join(work_dir, "data")
    
    logs = []
    
    msg_start = f"【提取智能体】 正在调用【文件扫描】完成工作：扫描目录 {data_dir}..."
    console.print(f"[bold blue]{msg_start}[/bold blue]")
    logs.append(msg_start)
    
    # 1. Detect File Type manually to pass to state (since tool returns string)
    # Re-implement simple detection logic here for state update
    pdfs = glob.glob(os.path.join(data_dir, "*.pdf"))
    docs = glob.glob(os.path.join(data_dir, "*.docx"))
    files = pdfs + docs
    
    file_ext = ""
    if files:
        file_ext = os.path.splitext(files[0])[1].lower()
        msg_detect = f"【提取智能体】 检测到简历文件：{os.path.basename(files[0])} ({file_ext})"
        console.print(f"[cyan]{msg_detect}[/cyan]")
        logs.append(msg_detect)
    
    # 2. Read Resume
    console.print("[cyan]【提取智能体】 正在调用【读取工具】完成工作：读取简历文件...[/cyan]")
    result = read_resume_tool.invoke({"directory": data_dir})
    
    if result.startswith("Error"):
        msg_err = f"【提取智能体】 错误：无法提取简历 - {result}"
        console.print(f"[bold red]{msg_err}[/bold red]")
        logs.append(msg_err)
        return {
            "original_resume_text": "", 
            "resume_file_extension": "",
            "progress": ["Extraction Failed"],
            "logs": logs
        }
    
    msg_success = f"【提取智能体】 完成【简历提取】工作：成功提取 {len(result)} 个字符。"
    console.print(f"[green]{msg_success}[/green]")
    logs.append(msg_success)
    
    # 3. Save Extracted Text
    output_path = os.path.join(work_dir, "Optimized_Output", "extracted_content.txt")
    msg_save = f"【提取智能体】 正在调用【保存工具】完成工作：保存原始内容到 {output_path}..."
    console.print(f"[cyan]{msg_save}[/cyan]")
    logs.append(msg_save)
    
    save_document_tool.invoke({"content": result, "file_path": output_path})
    
    return {
        "original_resume_text": result,
        "resume_file_extension": file_ext,
        "progress": ["Resume Extracted"],
        "logs": logs
    }
