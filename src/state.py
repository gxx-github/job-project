from typing import TypedDict, Annotated, List, Dict, Optional
import operator

class AgentState(TypedDict):
    # Inputs
    job_name: str
    job_age: str
    technology_stack: str
    work_dir: str
    
    # Intermediate Data
    resume_file_extension: str # .pdf or .docx
    original_resume_text: str
    optimized_resume_text: str
    optimization_summary: str
    self_intro: str
    interview_questions: str
    
    # Section outputs (Key: Agent Name, Value: Optimized Content)
    sections: Dict[str, str]
    
    # Memory & Versioning
    memory_hits: Annotated[List[str], operator.add] # Track which sections used memory
    version: str # e.g. "v1.0"
    
    # Status Tracking
    progress: Annotated[List[str], operator.add] # Append-only list
    logs: Annotated[List[str], operator.add] # Append-only detailed logs
