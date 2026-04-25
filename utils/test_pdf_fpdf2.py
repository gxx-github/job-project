import os
from fpdf import FPDF
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

def test_fpdf2_generation():
    # 1. 设置路径
    base_dir = r"c:\Users\IT屌丝\Desktop\闲鱼知识专区\Langraph框架学习\Code\Job"
    original_font_path = os.path.join(base_dir, "fonts", "simhei.ttf")
    output_path = os.path.join(base_dir, "utils", "test_output_fpdf2.pdf")

    print(f"Font Path: {original_font_path}")
    if not os.path.exists(original_font_path):
        print("Error: Font file not found!")
        return

    # 2. 初始化 FPDF
    pdf = FPDF()
    pdf.add_page()

    # 3. 添加字体
    # FPDF2 支持直接加载 TTF，并且可以指定 style='' (regular), 'B' (bold), 'I' (italic)
    # 我们这里把同一个 simhei.ttf 注册为三种样式，以便支持 Markdown 的加粗/斜体语法
    try:
        pdf.add_font("SimHei", style="", fname=original_font_path)
        pdf.add_font("SimHei", style="B", fname=original_font_path)
        pdf.add_font("SimHei", style="I", fname=original_font_path)
        pdf.add_font("SimHei", style="BI", fname=original_font_path)
        print("Fonts registered successfully.")
    except Exception as e:
        print(f"Error registering font: {e}")
        return

    # 4. 设置字体
    pdf.set_font("SimHei", size=14)

    # 5. 写入内容 (使用 multi_cell 并开启 markdown=True)
    # FPDF2 的 Markdown 支持非常适合这个场景
    markdown_text = """
# 简历测试 (FPDF2 Version)

## 个人信息
- 姓名: **张三** (Zhang San)
- 职位: Python 工程师

## 技能 (Skills)
- **编程语言**: Python, JavaScript, Go (Bold Test - 加粗测试)
- *框架*: Django, Flask, React (Italic Test - 斜体测试)
- ***综合***: Bold and Italic (粗斜体测试)

## 详细介绍
这是一个测试文档，使用 **fpdf2** 库生成。
This is a test document to verify PDF generation using fpdf2.

代码块示例:
    def hello():
        print("你好，世界")
    """

    # 注意：fpdf2 的 markdown 支持还是实验性的，且语法有限。
    # 对于简单的加粗和斜体是支持的。标题可能需要手动处理大小，或者使用 HTMLMixin。
    # 这里我们演示最基础的 markdown=True
    
    try:
        pdf.multi_cell(w=0, h=10, txt=markdown_text, markdown=True)
        print("Content written to PDF.")
    except Exception as e:
        print(f"Error writing content: {e}")
        return

    # 6. 保存
    try:
        pdf.output(output_path)
        print(f"PDF generated successfully at: {output_path}")
    except Exception as e:
        print(f"Error saving PDF: {e}")

if __name__ == "__main__":
    test_fpdf2_generation()
