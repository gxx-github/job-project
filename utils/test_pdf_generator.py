
import os
import logging
import markdown
import shutil
import tempfile
from xhtml2pdf import pisa
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_generation_safe_path():
    # 1. 设置源路径
    base_dir = r"c:\Users\IT屌丝\Desktop\闲鱼知识专区\Langraph框架学习\Code\Job"
    original_font_path = os.path.join(base_dir, "fonts", "simhei.ttf")
    output_path = os.path.join(base_dir, "utils", "test_output_safe.pdf")
    
    print(f"Original Font Path: {original_font_path}")
    if not os.path.exists(original_font_path):
        print("Error: Font file not found!")
        return

    # 2. 【关键步骤】将字体复制到临时目录（纯英文路径）
    # 这一步是为了解决 ReportLab/xhtml2pdf 在处理中文路径时可能出现的底层编码错误
    try:
        # 创建一个临时文件，关闭自动删除，以便我们手动控制
        # delete=False 是必须的，因为我们要多次读取它（注册多次）
        tmp_fd, tmp_font_path = tempfile.mkstemp(suffix=".ttf")
        os.close(tmp_fd) # 关闭文件描述符，只保留路径
        
        # 复制内容
        shutil.copy2(original_font_path, tmp_font_path)
        print(f"Font copied to temporary path: {tmp_font_path}")
        
    except Exception as e:
        print(f"Error copying font to temp: {e}")
        return

    # 3. 在 ReportLab 中注册这个临时路径的字体
    font_family = "SimHeiSafe" # 使用一个唯一的字体名
    
    try:
        # 注册主字体
        pdfmetrics.registerFont(TTFont(font_family, tmp_font_path))
        
        # 注册变体 (全部映射到同一个 .ttf 文件)
        pdfmetrics.registerFont(TTFont(f"{font_family}-Bold", tmp_font_path))
        pdfmetrics.registerFont(TTFont(f"{font_family}-Italic", tmp_font_path))
        pdfmetrics.registerFont(TTFont(f"{font_family}-BoldItalic", tmp_font_path))
        
        # 建立映射
        addMapping(font_family, 0, 0, font_family)              # Regular
        addMapping(font_family, 1, 0, f"{font_family}-Bold")      # Bold
        addMapping(font_family, 0, 1, f"{font_family}-Italic")    # Italic
        addMapping(font_family, 1, 1, f"{font_family}-BoldItalic")# BoldItalic
        
        print(f"Successfully registered font '{font_family}' from temp path.")
        
    except Exception as e:
        print(f"Error registering font: {e}")
        # 清理临时文件
        if os.path.exists(tmp_font_path):
            os.unlink(tmp_font_path)
        return

    # 4. 准备测试内容
    markdown_content = """
# 简历测试 - Resume Test (Safe Path)

## 个人信息
- 姓名: 张三 (Zhang San)
- 职位: Python 工程师

## 技能 (Skills)
- **编程语言**: Python, JavaScript, Go (Bold Test - 加粗测试)
- *框架*: Django, Flask, React (Italic Test - 斜体测试)
- ***综合***: Bold and Italic (粗斜体测试)

## 详细介绍
这是一个测试文档，用于验证 PDF 生成是否会出现乱码。
This is a test document to verify PDF generation using a temporary font file path.

Code Block:
```python
def hello():
    print("你好，世界")
```
    """

    # 5. 转换为 HTML
    html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
    
    # 6. 构建 CSS 和 HTML
    # 注意：这里只使用 font-family 名称，不使用 src: url()，避免 xhtml2pdf 去加载文件
    
    css_style = f"""
    <style>
        html, body {{
            font-family: '{font_family}', sans-serif;
            font-size: 12pt;
        }}
        
        h1, h2, h3 {{
            font-family: '{font_family}';
            font-weight: bold;
        }}
        
        code {{
            font-family: '{font_family}';
        }}
        
        pre {{
            font-family: '{font_family}';
            background-color: #f0f0f0;
            padding: 10px;
        }}
        
        /* 强制指定加粗/斜体样式对应的字体族 */
        strong, b {{
            font-family: '{font_family}';
            font-weight: bold;
        }}
        
        em, i {{
            font-family: '{font_family}';
            font-style: italic;
        }}
    </style>
    """
    
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        {css_style}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # 7. 生成 PDF
    print(f"Generating PDF to: {output_path}")
    try:
        with open(output_path, "wb") as result_file:
            pisa_status = pisa.CreatePDF(
                final_html, 
                dest=result_file, 
                encoding='utf-8'
            )
        
        if pisa_status.err:
            print(f"Error generating PDF: {pisa_status.err}")
        else:
            print("PDF generation successful!")
            print(f"Check output at: {output_path}")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_font_path):
            try:
                os.unlink(tmp_font_path)
                print("Temporary font file cleaned up.")
            except:
                pass

if __name__ == "__main__":
    test_pdf_generation_safe_path()
