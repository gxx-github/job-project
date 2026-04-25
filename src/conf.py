import os

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 自我介绍配置
SELF_INTRO_LENGTH = 200 # 自我介绍目标字数
SELF_INTRO_INDENT_CHARS = 2 # 自我介绍首行缩进字符数 (在Prompt中控制，非渲染层)

# 记忆模块配置
ENABLE_MEMORY = True # 是否启用记忆增强
CLEAR_MEMORY_ON_START = False # 是否在启动时清除历史记忆
MEMORY_DIR = os.path.join(BASE_DIR, "data", "memory_store") # 记忆存储路径

# 面试题生成配置
TOTAL_INTERVIEW_QUESTIONS = 1
QUESTIONS_PER_BATCH = 1

# PDF生成配置
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
PDF_FONT_NAME = "simhei.ttf"

# PDF 样式配置
PDF_TITLE_SIZE = 30
PDF_HEADER_SIZE = 20
PDF_SUBHEADER_SIZE = 16
PDF_PROJECT_SUBHEADER_SIZE = 14
PDF_BODY_FONT_SIZE = 12

PDF_TITLE_STYLE = 'B'
PDF_HEADER_STYLE = 'B'
PDF_SUBHEADER_STYLE = 'B'
PDF_PROJECT_SUBHEADER_STYLE = 'B'

PDF_LINE_HEIGHT = 10
PDF_LIST_INDENT = 8
PDF_SELF_INTRO_INDENT = 8 # mm

# 个人信息默认值
DEFAULT_SALARY = "面议"
DEFAULT_IS_RESIGNED = "是"

# 证书默认值
DEFAULT_CERT_DATE = "2017"
DEFAULT_CERT_ORG = "中国计算机研究机构"

# 智能体独立配置 (Section Specific Configs)
SECTION_CONFIGS = {
    "title": {
        "style": "B",
        "size": 30,
        "align": "C"
    },
    "personal_info": {
        # 个人信息特定配置
    },
    "skills": {
        "force_list": False,
        "ident": False
    },
    "certificate": {
        "force_list": False,
    },
    "work_experience": {
        "ident": False
    },
    "project_experience": {
        "subheader_style": "B",
        "indent_description": True,
    },
    "self_introduction": {
        "length_limit": SELF_INTRO_LENGTH,
        "indent": True,
        "indent_size": 8, # mm
    }
}
