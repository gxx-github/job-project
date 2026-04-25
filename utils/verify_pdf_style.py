import os
import sys
import logging

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.tools.pdf_ops import generate_pdf_tool

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_style():
    output_path = os.path.join(project_root, "utils", "test_style_output.pdf")
    
    # Sample Markdown Content simulating Structure Agent output with new requirements
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
- 熟悉 **Docker**, **Kubernetes** 容器化技术。
- 深入理解 **微服务架构** 设计模式。

## 工作经历
**高级开发工程师 | 某互联网公司 | 2020-2023**
- **职责:** 负责核心交易系统重构，提升系统吞吐量 50%。
- **亮点:** 主导微服务拆分，将单体应用拆分为 12 个微服务。
- 
- 
- ###

## 项目经验
### 项目一：企业级知识库系统
- **项目描述:** 基于 **RAG** 技术构建的智能问答系统。
- **职责:** 设计向量检索策略，优化 Prompt 工程。

### 项目二：智能客服系统
- **难点:** 处理高并发场景下的 websocket 连接。
- **成果:** 实现了单机 10w+ 长连接支持。

## 自我介绍
十年开发经验，热爱技术，善于解决复杂问题。
"""
    
    print(f"Generating PDF to: {output_path}")
    try:
        result = generate_pdf_tool.invoke({"markdown_content": markdown_content, "output_path": output_path})
        print(f"Result: {result}")
        
        if "Successfully generated PDF" in result:
            print("✅ Style Generation Successful.")
            print(f"Please check {output_path} manually for font sizes, bold text, and layout.")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    verify_style()
