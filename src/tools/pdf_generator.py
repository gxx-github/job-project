import os
import re
import html
from rich.console import Console
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT

from src.conf import (
    FONTS_DIR, PDF_FONT_NAME,
    PDF_TITLE_SIZE, PDF_HEADER_SIZE, PDF_SUBHEADER_SIZE, PDF_PROJECT_SUBHEADER_SIZE, PDF_BODY_FONT_SIZE,
    PDF_LINE_HEIGHT, PDF_LIST_INDENT
)

console = Console()

# 注册字体
def register_fonts():
    font_path = os.path.join(FONTS_DIR, PDF_FONT_NAME)
    if not os.path.exists(font_path):
        console.print(f"[red]Error: Font file not found at {font_path}[/red]")
        return False
    
    try:
        pdfmetrics.registerFont(TTFont('SimHei', font_path))
        # 注册粗体 (简单起见复用同一个字体，实际应该用专门的粗体文件)
        pdfmetrics.registerFont(TTFont('SimHei-Bold', font_path)) 
        return True
    except Exception as e:
        console.print(f"[red]Font registration failed: {e}[/red]")
        return False

def convert_markdown_to_pdf(markdown_content: str, output_path: str) -> bool:
    """
    使用 ReportLab Platypus 将 Markdown 内容转换为 PDF。
    彻底解决 fpdf2 的 "Not enough horizontal space" 问题。
    """
    if not register_fonts():
        return False

    try:
        # 1. 样式定义
        styles = getSampleStyleSheet()
        
        # 基础正文样式
        style_body = ParagraphStyle(
            name='Body',
            fontName='SimHei',
            fontSize=PDF_BODY_FONT_SIZE,
            leading=PDF_LINE_HEIGHT * 1.6, # 行间距加大到 1.6
            firstLineIndent=0,
            alignment=TA_LEFT,
            spaceAfter=8 # 增加段后距
        )
        
        # 标题样式
        style_title = ParagraphStyle(
            name='ResumeTitle',
            parent=style_body,
            fontSize=PDF_TITLE_SIZE,
            alignment=TA_CENTER,
            spaceAfter=30, # 增加标题后间距
            fontName='SimHei-Bold'
        )
        
        style_h2 = ParagraphStyle(
            name='SectionHeader',
            parent=style_body,
            fontSize=PDF_HEADER_SIZE,
            fontName='SimHei-Bold',
            spaceBefore=25, # 增加段前距
            spaceAfter=20,  # 增加段后距
        )
        
        style_h3 = ParagraphStyle(
            name='SubHeader',
            parent=style_body,
            fontSize=PDF_SUBHEADER_SIZE,
            fontName='SimHei-Bold',
            spaceBefore=15, # 增加段前距
            spaceAfter=10   # 增加段后距
        )

        # 项目三级标题样式 (移除加粗)
        style_project_key = ParagraphStyle(
            name='ProjectKey',
            parent=style_body,
            fontName='SimHei', # 使用普通字体
            fontSize=PDF_BODY_FONT_SIZE,
        )

        # 自我评价样式 (首行缩进)
        style_indent = ParagraphStyle(
            name='IndentBody',
            parent=style_body,
            firstLineIndent=2 * PDF_BODY_FONT_SIZE, # 2个字符宽度
            alignment=TA_JUSTIFY,
            leading=PDF_LINE_HEIGHT * 1.6 # 保持与正文一致
        )
        
        # 列表内容样式 (统一使用标准正文样式，不再使用紧凑样式)
        style_list_content = style_body # 直接复用 style_body，确保与正文一致

        # 专业技能样式 (加大行距)
        style_skill_content = ParagraphStyle(
            name='SkillContent',
            parent=style_body,
            leading=PDF_LINE_HEIGHT * 2.0, # 加大到 2.0 倍
            spaceAfter=5
        )

        # 2. 解析 Markdown 为 Flowables
        story = []
        lines = markdown_content.split('\n')
        i = 0
        current_section = None
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # --- 标题 ---
            if line.startswith('# '):
                story.append(Paragraph(line[2:].strip(), style_title))
                current_section = "title"
                
            elif line.startswith('## '):
                # H2 标题 (移除下划线)
                title_text = line[3:].strip()
                
                # 直接使用 Paragraph，移除 Table 和下划线
                story.append(Spacer(1, 15)) # 增加段前距
                story.append(Paragraph(title_text, style_h2))
                story.append(Spacer(1, 5))  # 增加段后距
                
                # 识别板块
                if "个人信息" in title_text: current_section = "personal_info"
                elif "职业经历" in title_text: current_section = "work_experience"
                elif "教育经历" in title_text: current_section = "education"
                elif "技能证书" in title_text: current_section = "certificate"
                elif "专业技能" in title_text: current_section = "skills"
                elif "项目经验" in title_text: current_section = "projects"
                elif "自我评价" in title_text: current_section = "self_eval"
                else: current_section = "other"
                
            # --- 板块内容 ---
            
            # 1. 个人信息 (双列布局)
            elif current_section == "personal_info":
                info_items = []
                # 收集所有行
                while i < len(lines) and not lines[i].startswith('#'):
                    l = lines[i].strip()
                    if l:
                        l = l.replace('**', '').replace('- ', '').replace('*', '')
                        if '：' in l or ':' in l:
                            info_items.append(l)
                    i += 1
                i -= 1 # Backtrack for outer loop
                
                # 构建表格数据
                table_data = []
                for idx in range(0, len(info_items), 2):
                    row = []
                    row.append(Paragraph(info_items[idx], style_body))
                    if idx + 1 < len(info_items):
                        row.append(Paragraph(info_items[idx+1], style_body))
                    else:
                        row.append("")
                    table_data.append(row)
                
                if table_data:
                    t = Table(table_data, colWidths=['50%', '50%'])
                    t.setStyle(TableStyle([
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('LEFTPADDING', (0,0), (-1,-1), 0),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                    ]))
                    story.append(t)

            # 2. 三列布局 (职业/教育)
            elif current_section in ["work_experience", "education", "certificate"]:
                if '|' in line:
                    parts = [p.strip() for p in line.replace('- ', '').split('|')]
                    if len(parts) >= 3:
                        # Role | Company | Date
                        # 35% | 40% | 25%
                        col1 = Paragraph(f"<b>{parts[0]}</b>", style_body)
                        col2 = Paragraph(parts[1], style_body)
                        col3 = Paragraph(parts[2], ParagraphStyle('Right', parent=style_body, alignment=TA_RIGHT))
                        
                        t = Table([[col1, col2, col3]], colWidths=['35%', '40%', '25%'])
                        t.setStyle(TableStyle([
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                            ('ALIGN', (2,0), (2,0), 'RIGHT'),
                            ('LEFTPADDING', (0,0), (-1,-1), 0),
                            ('RIGHTPADDING', (-1,-1), (-1,-1), 0),
                        ]))
                        story.append(t)
                    elif len(parts) == 2:
                        col1 = Paragraph(f"<b>{parts[0]}</b>", style_body)
                        col2 = Paragraph(parts[1], ParagraphStyle('Right', parent=style_body, alignment=TA_RIGHT))
                        t = Table([[col1, col2]], colWidths=['50%', '50%'])
                        story.append(t)
                    else:
                        story.append(Paragraph(line, style_body))
                else:
                    story.append(Paragraph(line, style_body))

            # 3. 项目经验
            elif current_section == "projects":
                clean_line = line.replace('**', '').replace('###', '').strip()
                clean_line = re.sub(r'^#+\s*', '', clean_line).strip()
                
                # 优先匹配子字段 Key (项目描述、技术栈、职责、项目亮点)
                # 必须放在项目标题检测之前，因为 "项目描述" 也以 "项目" 开头，容易被误判为标题
                if any(clean_line.startswith(k) for k in ["项目描述", "技术栈", "职责", "项目亮点"]):
                    # Key: Value
                    parts = clean_line.split(':', 1)
                    if len(parts) < 2: parts = clean_line.split('：', 1)
                    
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip()
                        
                        # 彻底清洗和转义，防止任何隐式格式化
                        # 去除可能的加粗标记
                        key = key.replace('**', '').replace('__', '')
                        val = val.replace('**', '').replace('__', '')
                        
                        # 转义 HTML 特殊字符，防止 <, >, & 等被解析为标签
                        key = html.escape(key)
                        val = html.escape(val)
                        
                        # 使用 Table 实现 Key: Value 布局
                        
                        # 统一字体大小: style_body (12pt)
                        # 项目经验子标题: Key 不加粗，使用普通字体 (用户要求)
                        p_key = Paragraph(f"{key}：", style_body)
                        
                        # Value 处理：如果是职责或亮点，需要处理成列表格式
                        # 但这里 val 是整段文本。如果包含 "1. "，需要分割？
                        # 现在的逻辑是把整段作为 value。
                        # 如果 value 中包含换行符（被之前的清洗逻辑合并了），或者包含 1. 2. 
                        # 我们最好直接渲染 val。
                        
                        p_val = Paragraph(val, style_body)
                        
                        t = Table([[p_key, p_val]], colWidths=[25*mm, None]) 
                        t.setStyle(TableStyle([
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('LEFTPADDING', (0,0), (-1,-1), 0),
                            ('RIGHTPADDING', (0,0), (-1,-1), 0),
                        ]))
                        story.append(t)
                        
                        # 如果是职责或亮点，且内容是 1. 2. 格式，可能需要拆分？
                        # 但 section_agents.py 里已经把它们合并成一行了？
                        # 之前的逻辑：cleaned_lines.append(line) -> 合并
                        # 用户要求 "1.内容 2.内容"
                        # 现在的 val 可能是 "1. 内容一 2. 内容二"
                        # 这样显示在一行是可以的，符合 "填满整行" 的要求。
                    else:
                        story.append(Paragraph(clean_line, style_body))

                elif line.startswith('###') or line.startswith('项目') or clean_line.startswith('项目一') or clean_line.startswith('项目二'):
                    # H3 (项目标题)
                    story.append(Spacer(1, 5))
                    clean_line = clean_line.replace('：', ' ').replace(':', ' ')
                    story.append(Paragraph(clean_line, style_h3))
                        
                elif line.strip().startswith('-') or re.match(r'^\d+\.', line.strip()):
                    # 列表 (针对非项目经验部分的列表，或者项目经验中漏网的)
                    # 尝试检测是否有序
                    match = re.match(r'^(\d+\.)', line.strip())
                    if match:
                        bullet_text = match.group(1)
                        content = line.strip()[len(bullet_text):].strip()
                    else:
                        bullet_text = "•"
                        content = line.strip().lstrip('-').strip()
                    
                    # 转义内容，防止 HTML 标签解析
                    content = html.escape(content)
                    
                    bullet = Paragraph(bullet_text, style_body)
                    content_p = Paragraph(content, style_list_content) # 使用紧凑样式
                    t = Table([[bullet, content_p]], colWidths=[10*mm, None]) # 增加宽度以容纳数字
                    t.setStyle(TableStyle([
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ]))
                    story.append(t)
                else:
                    story.append(Paragraph(line, style_body))

            # 4. 自我评价
            elif current_section == "self_eval":
                full_text = []
                while i < len(lines) and not lines[i].startswith('#'):
                    l = lines[i].strip().replace(" ", "")
                    if l: full_text.append(l)
                    i += 1
                i -= 1
                
                text_block = "".join(full_text)
                if text_block:
                    story.append(Paragraph(text_block, style_indent))

            # 5. 专业技能
            elif current_section == "skills":
                if line.startswith('- '):
                    content = line[2:].strip()
                    bullet = Paragraph("•", style_body)
                    # 使用 style_skill_content
                    p = Paragraph(content, style_skill_content)
                    t = Table([[bullet, p]], colWidths=[5*mm, None])
                    t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
                    story.append(t)
                else:
                    story.append(Paragraph(line, style_skill_content))

            else:
                # Default
                story.append(Paragraph(line, style_body))
                
            i += 1
            
        # 3. 生成 PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        doc.build(story)
        
        console.print(f"[green]PDF successfully generated using ReportLab at: {output_path}[/green]")
        return True

    except Exception as e:
        console.print(f"[bold red]Exception in PDF generation (ReportLab): {str(e)}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        import sys
        sys.exit(1)
