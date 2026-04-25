
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.pdf_generator import convert_markdown_to_pdf

def verify_fix():
    print("开始验证 PDF 生成 (fpdf2)...")
    
    # 测试内容包含中文、标点符号、加粗
    markdown_content = """
# 简历生成测试 (Test)

## 个人信息
- **姓名**: 张三 (Zhang San)
- **职位**: 高级 Python 工程师
- **电话**: 13800138000

## 自我介绍
拥有 5 年 Python 开发经验，熟悉 Django/Flask 框架。
擅长解决复杂的技术问题，具有良好的团队协作能力。

## 项目经验
### 1. 智能简历生成系统
- **角色**: 核心开发者
- **描述**: 基于 LLM 的简历优化与生成工具。
- **成果**: 解决了 PDF 生成过程中的**中文乱码**问题，提升了用户体验。
    """
    
    output_path = os.path.join(os.path.dirname(__file__), "verify_output_fpdf2.pdf")
    
    # 清理旧文件
    if os.path.exists(output_path):
        os.remove(output_path)
        
    try:
        success = convert_markdown_to_pdf(markdown_content, output_path)
        
        if success and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"\n[成功] PDF 已生成: {output_path}")
            print(f"文件大小: {file_size} bytes")
            if file_size > 1000:
                print("文件大小正常，内容应该已写入。")
            else:
                print("[警告] 文件过小，可能为空。")
        else:
            print("\n[失败] PDF 生成函数返回 False 或文件未创建。")
            
    except Exception as e:
        print(f"\n[异常] 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_fix()
