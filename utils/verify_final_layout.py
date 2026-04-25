import os
import sys
import logging

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.tools.pdf_ops import generate_pdf_tool

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_final_layout():
    output_path = os.path.join(project_root, "utils", "test_final_layout.pdf")
    
    # Sample Markdown simulating Structure Agent output with NEW requirements
    markdown_content = """# 求职简历

## 个人信息
```json
{
    "姓名": "王亮",
    "年龄": "32",
    "性别": "男性",
    "学历": "本科",
    "电话": "13800138000",
    "邮箱": "wangliang@example.com",
    "工作年限": "10年",
    "求职意向": "高级Python开发"
}
```

## 专业技能
- 精通 **Python** 开发，熟悉 FastAPI, Django 框架。

## 工作经历
高级开发工程师 | 某互联网公司 | 2020.06 - 2023.12
Python 研发 | 北京新纽科技有限公司 | 2022.08 - 2024.07
Python 研发 | 北京美信时代科技有限公司 | 2020.08 - 2022.06
Python 研发 | 中软国际有限公司 | 2018.05 - 2020.06

## 项目经验
### 项目一：企业级知识库系统
高级开发工程师 | 某互联网公司 | 2020.06 - 2023.12
- **项目描述:** 基于 **RAG** 技术构建的智能问答系统。
- **技术栈:** **LangChain**, **Milvus**, **FastAPI**, **Redis**
- **职责:** 
    - 1. 数据准备与索引，构建千万级向量数据库。
    - 2. 设计向量检索策略，实现多路召回。
- **项目亮点:** 
    - 检索准确率从 60% 提升至 90%。

## 自我介绍
十年开发经验，热爱技术，善于解决复杂问题。具有丰富的分布式系统设计经验。
对大模型应用落地有深入理解。
"""
    
    print(f"Generating PDF to: {output_path}")
    try:
        result = generate_pdf_tool.invoke({"markdown_content": markdown_content, "output_path": output_path})
        print(f"Result: {result}")
        
        if "Successfully generated PDF" in result:
            print("✅ Final Layout Verification Successful.")
            print(f"Please check {output_path} manually.")
            print("Checklist:")
            print("1. Work Experience columns (Pos | Co | Time) should align perfectly vertically.")
            print("2. Project subheaders (Desc, Role, Highlights) should NOT have bullets and align left.")
            print("3. Self Intro first line should be indented.")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    verify_final_layout()
