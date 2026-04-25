"""
Agents dedicated to optimizing specific sections of the resume with Memory Enhancement.
"""
import os
import json
import re
from rich.console import Console
from src.state import AgentState
from src.llm.factory import get_llm
from src.prompts.section_prompts import (
    TITLE_PROMPT,
    PERSONAL_INFO_PROMPT,
    SKILLS_PROMPT,
    CERTIFICATE_PROMPT,
    WORK_EXP_PROMPT,
    EDUCATION_PROMPT,
    PROJECT_EXP_PROMPT,
    SELF_EVAL_PROMPT
)
from src.memory.manager import memory_manager
from src.conf import SECTION_CONFIGS, DEFAULT_SALARY, DEFAULT_IS_RESIGNED, SELF_INTRO_LENGTH, DEFAULT_CERT_DATE, DEFAULT_CERT_ORG
from src.tools.pdf_generator import convert_markdown_to_pdf # New tool
# from src.tools.pdf_ops import generate_pdf_tool # Deprecated

console = Console()

def clean_text_spacing(text: str) -> str:
    """
    通用文本清洗函数：
    1. 去除中文之间的空格
    2. 去除中文与英文/数字之间的空格
    3. 保留纯英文单词之间的空格
    """
    if not text:
        return text
        
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        if not line.strip():
            cleaned_lines.append(line)
            continue
            
        # 简单策略：先去除所有空格，再尝试恢复英文空格（太复杂）
        # 替代策略：
        # 1. 替换 "中 英" -> "中英"
        # 2. 替换 "中 1" -> "中1"
        # 3. 替换 "a 中" -> "a中"
        
        # 使用正则更稳健
        import re
        # 去除 中文-空格-中文
        line = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', line)
        # 去除 中文-空格-非中文
        line = re.sub(r'([\u4e00-\u9fa5])\s+([^\u4e00-\u9fa5])', r'\1\2', line)
        # 去除 非中文-空格-中文
        line = re.sub(r'([^\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', line)
        
        cleaned_lines.append(line)
        
    return '\n'.join(cleaned_lines)

def _run_section_agent(state: AgentState, section_key: str, prompt_template: str, config_key: str) -> dict:
    """
    Helper function to run a generic section agent with Memory Support.
    """
    logs = []
    agent_name = f"Agent-{section_key}"
    console.print(f"[cyan]【{agent_name}】 正在处理...[/cyan]")
    logs.append(f"【{agent_name}】 开始处理...")
    
    # 1. Prepare Data
    original_resume = state.get("original_resume_text", "")
    job_name = state.get("job_name", "")
    tech_stack = state.get("technology_stack", "")
    
    # 2. Check Memory First
    # Context for hash uniqueness (job_name/stack affects optimization result)
    memory_context = {"job_name": job_name, "technology_stack": tech_stack}
    
    # Special handling for self_eval: it depends on optimized summary of other sections
    if section_key == "self_evaluation":
        sections = state.get("sections", {})
        # Use summary of current sections as context for memory
        # We need a stable representation, so sort keys
        summary_str = json.dumps(sections, sort_keys=True, ensure_ascii=False)
        memory_context["sections_summary"] = summary_str
        
    cached_content = memory_manager.get_optimized_content(section_key, original_resume, memory_context)
    
    content = ""
    is_memory_hit = False
    
    if cached_content:
        console.print(f"[green]【{agent_name}】 命中记忆缓存，跳过LLM生成。[/green]")
        logs.append(f"【{agent_name}】 命中记忆缓存。")
        content = cached_content
        is_memory_hit = True
    else:
        # 3. Build Prompt (if no memory hit)
        format_args = {
            "resume_content": original_resume,
            "job_name": job_name,
            "job_age": state.get("job_age", "3年"), # Default if missing
            "technology_stack": tech_stack,
            "SELF_INTRO_LENGTH": SELF_INTRO_LENGTH,
            "default_cert_date": DEFAULT_CERT_DATE,
            "default_cert_org": DEFAULT_CERT_ORG
        }
        
        if section_key == "self_evaluation":
            sections = state.get("sections", {})
            summary = "\n".join([f"--- {k} ---\n{v}" for k, v in sections.items() if v])
            # Merge into format_args instead of overwriting
            format_args["optimized_sections_summary"] = summary

        try:
            prompt = prompt_template.format(**format_args)
            
            # 4. Call LLM
            llm = get_llm()
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            # 5. Clean up markdown fences
            if section_key != "personal_info":
                if content.startswith("```markdown"):
                    content = content.replace("```markdown", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()
                
                # Apply spacing cleanup for all text-based sections
                content = clean_text_spacing(content)
            
            # 5.1 Special Post-processing for specific sections
            if section_key == "personal_info":
                try:
                    # Clean up json block if needed
                    json_str = content
                    if json_str.startswith("```json"):
                        json_str = json_str.replace("```json", "", 1)
                    if json_str.startswith("```"):
                        json_str = json_str.replace("```", "", 1)
                    if json_str.endswith("```"):
                        json_str = json_str[:-3]
                    json_str = json_str.strip()
                    
                    data = json.loads(json_str)
                    
                    # Apply defaults if missing or empty
                    if not data.get("薪资待遇"):
                        data["薪资待遇"] = DEFAULT_SALARY
                    if not data.get("是否离职"):
                        data["是否离职"] = DEFAULT_IS_RESIGNED
                        
                    # CRITICAL: Force update Job Intention with user input
                    if job_name:
                         data["求职意向"] = job_name
                        
                    # Re-serialize to keep content consistent
                    # 转换为 Markdown 列表形式，PDF 生成器会解析它
                    
                    md_lines = []
                    # 定义输出顺序
                    order = ["姓名", "性别", "年龄", "电话", "邮箱", "学历", "求职意向", "现居地", "薪资待遇", "是否离职", "工作年限"]
                    
                    # 先添加有序字段
                    for k in order:
                        if k in data and data[k]:
                             # 不使用 **加粗**，PDF 生成器会统一处理
                             md_lines.append(f"{k}：{data[k]}")
                    
                    # 添加剩余字段
                    for k, v in data.items():
                        if k not in order and v:
                            md_lines.append(f"{k}：{v}")
                            
                    content = "\n".join(md_lines)
                    
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to parse/update personal_info JSON: {e}[/yellow]")

            elif section_key == "skills":
                # Force remove spaces in skill lines (except standard english spaces)
                # But clean_text_spacing already handled most.
                # Just ensure no indentation
                lines = [l.strip() for l in content.split('\n') if l.strip()]
                cleaned_lines = []
                for l in lines:
                     if not l.startswith("-"):
                         l = f"- {l}"
                     # Remove spaces inside the skill line if it looks like "Lin u x"
                     # Use the stricter cleaning
                     cleaned_lines.append(l)
                content = "\n".join(cleaned_lines)

            elif section_key == "certificate":
                # Ensure list format and defaults
                pass 

            elif section_key == "self_evaluation":
                # Remove all newlines to make it a single paragraph
                content = content.replace("\n", "").strip()
                # 再次清理空格
                content = clean_text_spacing(content)
                # 去除可能的首行缩进，让 PDF 生成器处理
                content = content.lstrip()
            
            elif section_key == "project_experience":
                # Clean up newlines within description and tech stack
                # We need to process line by line, identifying subheaders
                lines = content.split('\n')
                cleaned_lines = []
                current_block = []
                
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    # If it's a header or list item, flush current block and add line
                    # 识别 ### 项目标题
                    # 识别 描述: 技术栈: 职责: 亮点:
                    # 识别 - 列表
                    # 强制将项目标题转换为 "### 项目名" 格式 (虽然 PDF 生成器会再次清洗，但这里保证数据源规范)
                    if line.startswith("#"):
                        if current_block:
                             cleaned_lines.append("".join(current_block))
                             current_block = []
                        # 确保只有一个 ### 且后面有空格
                        # 简单清洗：去除所有 #，然后加 ###
                        clean_title = line.replace("#", "").strip()
                        cleaned_lines.append(f"### {clean_title}")
                        
                    elif any(line.startswith(k) for k in ["项目描述", "技术栈", "职责", "项目亮点"]):
                         if current_block:
                             cleaned_lines.append("".join(current_block))
                             current_block = []
                         cleaned_lines.append(line)
                         
                    elif line.startswith("-") or re.match(r"\d+\.", line):
                         # 强制转换为有序列表 1. 2. 3.
                         # 但这里不好计数，因为不知道是属于哪个块。
                         # 简单起见，如果原文本是 -，我们尝试保留 -，或者让 PDF 生成器统一处理。
                         # 用户要求 "1.内容 2.内容"，所以最好在这里转换。
                         # 但如果 LLM 输出的是无序列表，这里转换比较困难。
                         # 妥协：在 Prompt 中已经要求有序列表。这里只做简单的行合并防止断行。
                         if current_block:
                             cleaned_lines.append("".join(current_block))
                             current_block = []
                         cleaned_lines.append(line)
                    else:
                        # It's part of a paragraph (like description continuation), merge it
                        current_block.append(line)
                
                if current_block:
                    cleaned_lines.append("".join(current_block))
                
                content = "\n".join(cleaned_lines)
            
            # 6. Save to Memory (Disabled for interactive mode)
            # memory_manager.save_optimized_content(section_key, original_resume, content, memory_context)
            # console.print(f"[dim]【{agent_name}】 记忆保存已跳过 (等待用户确认)...[/dim]")
            
            logs.append(f"【{agent_name}】 处理完成 (LLM生成)。")
            console.print(f"[green]【{agent_name}】 完成。[/green]")
            
            # 增加调试日志输出
            debug_content = content[:500] + "..." if len(content) > 500 else content
            console.print(f"[dim]--- [{agent_name}] 生成内容预览 ---[/dim]")
            console.print(f"[dim]{debug_content}[/dim]")
            console.print(f"[dim]------------------------------------[/dim]")
            logs.append(f"【{agent_name}】 生成内容预览: {debug_content}")

        except Exception as e:
            error_msg = f"【{agent_name}】 错误: {str(e)}"
            console.print(f"[bold red]{error_msg}[/bold red]")
            logs.append(error_msg)
            return {"logs": logs}

    # 8. Generate Intermediate PDF (using new tool)
    if content and section_key != "title":
        try:
            work_dir = state.get("work_dir", ".")
            intermediate_dir = os.path.join(work_dir, "Optimized_Output", "intermediate")
            os.makedirs(intermediate_dir, exist_ok=True)
            
            pdf_filename = f"{section_key}_optimized.pdf"
            pdf_path = os.path.join(intermediate_dir, pdf_filename)
            
            # Wrap content with title for better rendering context
            temp_md = f"# {section_key.replace('_', ' ').title()}\n\n{content}"
            
            # Use NEW generate_pdf_tool
            convert_markdown_to_pdf(temp_md, pdf_path)
            logs.append(f"【{agent_name}】 中间结果PDF已保存: {pdf_filename}")
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to generate intermediate PDF for {section_key}: {e}[/yellow]")

    # 9. Update State
    current_sections = state.get("sections", {})
    if current_sections is None:
        current_sections = {}
    
    current_sections[section_key] = content
    
    # Update memory hits tracking
    memory_hits = state.get("memory_hits", [])
    if is_memory_hit:
        memory_hits.append(section_key)
    
    return {
        "sections": current_sections,
        "memory_hits": memory_hits,
        "logs": logs
    }

# --- Specific Agents ---

def title_agent(state: AgentState):
    return _run_section_agent(state, "title", TITLE_PROMPT, "title")

def personal_info_agent(state: AgentState):
    return _run_section_agent(state, "personal_info", PERSONAL_INFO_PROMPT, "personal_info")

def skills_agent(state: AgentState):
    return _run_section_agent(state, "skills", SKILLS_PROMPT, "skills")

def certificate_agent(state: AgentState):
    return _run_section_agent(state, "certificate", CERTIFICATE_PROMPT, "certificate")

def work_experience_agent(state: AgentState):
    return _run_section_agent(state, "work_experience", WORK_EXP_PROMPT, "work_experience")

def education_agent(state: AgentState):
    return _run_section_agent(state, "education", EDUCATION_PROMPT, "education")

def project_experience_agent(state: AgentState):
    return _run_section_agent(state, "project_experience", PROJECT_EXP_PROMPT, "project_experience")

def self_evaluation_agent(state: AgentState):
    return _run_section_agent(state, "self_evaluation", SELF_EVAL_PROMPT, "self_introduction")

def assembler_agent(state: AgentState):
    """Combines all sections into the final optimized resume."""
    logs = []
    console.print("[cyan]【Assembler】 正在组装简历...[/cyan]")
    
    sections = state.get("sections", {})
    
    # Define order
    # Title -> Personal Info -> Skills -> Work Exp -> Education -> Projects -> Self Eval
    
    # 1. Title (No header)
    title = sections.get("title", "求职简历")
    final_md = f"# {title}\n\n"
    
    # 2. Personal Info
    p_info = sections.get("personal_info", "")
    if p_info:
        final_md += "## 个人信息\n"
        final_md += p_info + "\n\n"
        
    # 3. Skills
    skills = sections.get("skills", "")
    if skills:
        final_md += "## 专业技能\n"
        final_md += skills + "\n\n"

    # 3.5 Certificate
    certs = sections.get("certificate", "")
    if certs and "无" not in certs:
        final_md += "## 技能证书\n"
        final_md += certs + "\n\n"
        
    # 4. Work Experience (renamed to 职业经历)
    work = sections.get("work_experience", "")
    if work:
        final_md += "## 职业经历\n"
        final_md += work + "\n\n"
        
    # 5. Education (New)
    edu = sections.get("education", "")
    if edu:
        final_md += "## 教育经历\n"
        final_md += edu + "\n\n"
        
    # 6. Project Experience
    proj = sections.get("project_experience", "")
    if proj:
        final_md += "## 项目经验\n"
        final_md += proj + "\n\n"
        
    # 7. Self Evaluation (renamed from Self Intro)
    intro = sections.get("self_evaluation", "")
    if intro:
        final_md += "## 自我评价\n"
        final_md += intro + "\n\n"
        
    # 8. Interactive Memory Management (Optional here, mostly handled in main.py)
    
    # 9. Final PDF Generation (using new tool)
    output_dir = os.path.join(state.get("work_dir", "."), "Optimized_Output")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "Optimized_Resume.pdf")
    
    try:
        if convert_markdown_to_pdf(final_md, pdf_path):
            logs.append(f"【Assembler】 PDF简历生成成功: {pdf_path}")
            console.print(f"[green]【Assembler】 PDF简历生成成功。[/green]")
        else:
            logs.append("【Assembler】 PDF简历生成失败。")
            console.print(f"[red]【Assembler】 PDF简历生成失败。[/red]")
    except Exception as e:
        console.print(f"[red]PDF generation error: {e}[/red]")
        logs.append(f"PDF generation error: {str(e)}")

    # 10. Save Markdown for reference
    md_path = os.path.join(output_dir, "optimized_resume.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(final_md)
        
    return {
        "optimized_resume_text": final_md,
        "logs": logs
    }
