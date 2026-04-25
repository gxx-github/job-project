import os
import sys
import logging

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.tools.pdf_ops import generate_pdf_tool

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_final_layout_v3():
    output_path = os.path.join(project_root, "utils", "test_final_layout_v3.pdf")
    
    # Sample Markdown testing all new requirements
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
- 熟练掌握 Python, Java (已有列表符)
熟悉 Docker, Kubernetes (无列表符，应被强制转换为列表)
- 精通 LangChain (已有列表符)

## 工作经历
高级开发工程师 | 某互联网公司 | 2020.06 - 2023.12
Python 研发 | 北京新纽科技有限公司 | 2022.08 - 2024.07

## 项目经验
### 项目一：企业级知识库系统
高级开发工程师 | 某互联网公司 | 2020.06 - 2023.12
**项目描述:** 本项目基于 RAG 技术构建。这是一个非常长的描述，用于测试首行缩进是否生效。如果不生效，第二行将不会对齐到左边距，或者第一行没有缩进。我们需要确保整个段落看起来是首行缩进的格式。
**技术栈:** Python, LangChain, Elasticsearch
**职责:**
1. 负责数据清洗。
2. 负责检索优化。
**项目亮点:**
1. 提升了检索准确率。

### 项目二：测试项目
**项目描述:** 测试行内描述。
**职责:**
- 职责一
- 职责二

## 自我介绍
本人拥有十年开发经验。
热爱技术，追求卓越。
这是第三行，应该合并为同一段落，并且只有第一行有缩进。
"""
    
    print(f"Generating PDF to: {output_path}")
    try:
        result = generate_pdf_tool.invoke({"markdown_content": markdown_content, "output_path": output_path})
        print(f"Result: {result}")
        
        if "Successfully generated PDF" in result:
            print("✅ Verification V3 Successful.")
            print(f"Please check {output_path} manually.")
            print("Checklist:")
            print("1. '专业技能': All 3 lines should be bullet points.")
            print("2. '工作经历': No indentation, aligned left.")
            print("3. '项目经验': '项目描述' content should be indented. '职责' list should NOT be indented (paragraph-wise).")
            print("4. '自我介绍': All 3 lines merged into one paragraph, only first line indented.")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    verify_final_layout_v3()
