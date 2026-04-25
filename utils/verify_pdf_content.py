import fitz  # PyMuPDF
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

def verify_pdf_content(pdf_path):
    print(f"Verifying PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False

    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        
        print("\n--- Extracted Text Content ---")
        print(text)
        print("------------------------------\n")
        
        # 验证关键词
        keywords = ["张三", "你好", "世界", "简历测试"]
        missing = []
        for kw in keywords:
            if kw not in text:
                missing.append(kw)
        
        if not missing:
            print("✅ SUCCESS: All Chinese keywords found! No mojibake detected.")
            return True
        else:
            print(f"❌ FAILURE: Missing keywords: {missing}. Mojibake likely present.")
            return False
            
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return False

if __name__ == "__main__":
    # 验证 fpdf2 生成的 PDF
    base_dir = r"c:\Users\IT屌丝\Desktop\闲鱼知识专区\Langraph框架学习\Code\Job"
    pdf_path = os.path.join(base_dir, "utils", "test_output_fpdf2.pdf")
    verify_pdf_content(pdf_path)
