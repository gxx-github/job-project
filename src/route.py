import os
from rich.console import Console
from src.llm.factory import get_llm

console = Console()

def route_job_to_tech_stack(job_name: str, tech_stack_dir: str) -> str:
    """
    Routes the user's job input to the most appropriate technology stack file.
    Uses a combination of Rule-Based Matching and Semantic Matching (LLM).
    """
    job_lower = job_name.lower()
    
    # --- 1. Rule-Based Matching (Priority Order) ---
    # We define strict rules here. Order matters!
    # Specific > General
    
    rules = [
        # Java + LLM/AI
        (lambda j: "java" in j and ("大模型" in j or "llm" in j or "ai" in j), "java_llm.txt"),
        
        # Python + LLM/AI
        (lambda j: "python" in j and ("大模型" in j or "llm" in j or "ai" in j), "llm_app_dev.txt"),
        
        # Pure LLM/AI (assume Python if not specified)
        (lambda j: "大模型" in j or "llm" in j, "llm_app_dev.txt"),
        
        # Java Backend
        (lambda j: "java" in j, "java_backend.txt"),
        
        # Python Backend
        (lambda j: "python" in j, "python_backend.txt"),
        
        # Frontend
        (lambda j: "前端" in j or "frontend" in j or "vue" in j or "react" in j, "frontend.txt"),
        
        # Testing
        (lambda j: "测试开发" in j or "测开" in j, "test_dev.txt"),
        (lambda j: "测试" in j or "qa" in j, "testing_manual.txt"),
        
        # DevOps / SRE
        (lambda j: "运维开发" in j or "sre" in j, "sre.txt"),
        (lambda j: "运维" in j or "devops" in j, "devops.txt"),
        
        # Product
        (lambda j: "产品" in j or "pm" in j, "product_manager.txt"),
        
        # General Backend (Fallback if 'backend' is mentioned but no language)
        # Defaulting to Java or Python? Let's check for "backend" or "后端"
        # If just "后端", rule-based might be ambiguous. Let Semantic handle it or default.
        (lambda j: "后端" in j and "python" not in j and "java" not in j, "java_backend.txt"), # Default to Java for generic backend in China? Or let LLM decide.
    ]
    
    for matcher, filename in rules:
        if matcher(job_lower):
            console.print(f"[cyan]路由匹配:[/cyan] 规则命中 -> {filename}")
            return filename

    # --- 2. Semantic Matching (LLM) ---
    console.print(f"[yellow]路由匹配:[/yellow] 规则未命中，尝试语义匹配...")
    
    try:
        # Get list of available files
        if not os.path.exists(tech_stack_dir):
            return "technology_stack.txt"
            
        files = [f for f in os.listdir(tech_stack_dir) if f.endswith(".txt")]
        if not files:
            return "technology_stack.txt"
            
        llm = get_llm()
        
        prompt = f"""
        你是一个智能路由助手。
        用户输入的工作岗位是: "{job_name}"
        
        现有的技术栈文件列表如下:
        {", ".join(files)}
        
        请分析用户的岗位名称，从列表中选择**最匹配**的一个文件名。
        
        只输出文件名，不要包含任何其他文字。
        如果无法确定，请输出 "technology_stack.txt"。
        """
        
        response = llm.invoke(prompt)
        matched_file = response.content.strip()
        
        # Basic validation
        if matched_file in files:
            console.print(f"[green]语义匹配:[/green] LLM命中 -> {matched_file}")
            return matched_file
        else:
            console.print(f"[red]语义匹配:[/red] LLM返回了无效文件名 '{matched_file}'，回退到默认。")
            
    except Exception as e:
        console.print(f"[bold red]语义匹配出错:[/bold red] {e}")
        
    return "technology_stack.txt"
