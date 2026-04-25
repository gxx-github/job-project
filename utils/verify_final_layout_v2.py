import os
import sys
import logging

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.tools.pdf_ops import generate_pdf_tool

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_final_layout_v2():
    output_path = os.path.join(project_root, "utils", "test_final_layout_v2.pdf")
    
    # Sample Markdown with NEW requirements
    markdown_content = """# 求职简历

## 个人信息
```json
{
    "姓名": "王亮",
    "年龄": "32",
    "性别": "男性",
    "学历": "本科"
}
```

## 专业技能
- 精通 **Python** 开发。

## 工作经历
高级开发工程师 | 某互联网公司 | 2020.06 - 2023.12
Python 研发 | 北京新纽科技有限公司 | 2022.08 - 2024.07

## 项目经验
### 项目一：企业级知识库系统
高级开发工程师 | 某互联网公司 | 2020.06 - 2023.12
1. **项目描述:** 基于 **RAG** 技术构建的智能问答系统。
2. **职责:** 1. 数据准备与索引。2. 检索策略。
3. **项目亮点:** 准确率 90%。

## 自我介绍
十年开发经验，热爱技术。
对大模型应用落地有深入理解。
"""
    
    print(f"Generating PDF to: {output_path}")
    try:
        result = generate_pdf_tool.invoke({"markdown_content": markdown_content, "output_path": output_path})
        print(f"Result: {result}")
        if "Successfully generated PDF" in result:
            print("✅ Verification V2 Successful.")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    verify_final_layout_v2()
