from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.agents.extractor import extractor_agent
from src.agents.layout_expert import layout_expert_agent
from src.agents.interviewer import interviewer_agent
from src.agents.section_agents import (
    title_agent,
    personal_info_agent,
    skills_agent,
    certificate_agent,
    work_experience_agent,
    education_agent,
    project_experience_agent,
    self_evaluation_agent,
    assembler_agent
)

def check_extraction_success(state: AgentState):
    """
    Conditional edge to check if resume extraction was successful.
    """
    resume_text = state.get("original_resume_text", "")
    if not resume_text or (state["logs"] and "Error" in state["logs"][-1]):
        return "end"
    return "continue"

def create_graph():
    """
    Constructs the Multi-Agent Workflow Graph with Section-Based Optimization and Memory Enhancement.
    """
    workflow = StateGraph(AgentState)
    
    # 1. Input Layer
    workflow.add_node("extractor", extractor_agent)
    
    # 2. Optimization Layer (Section Agents)
    # Each agent internally handles Memory Hit (Cache) vs LLM Generation
    workflow.add_node("title", title_agent)
    workflow.add_node("personal_info", personal_info_agent)
    workflow.add_node("skills", skills_agent)
    workflow.add_node("certificate", certificate_agent)
    workflow.add_node("work_experience", work_experience_agent)
    workflow.add_node("education", education_agent)
    workflow.add_node("project_experience", project_experience_agent)
    workflow.add_node("self_evaluation", self_evaluation_agent)
    
    # 3. Output Layer
    workflow.add_node("assembler", assembler_agent)
    workflow.add_node("layout_expert", layout_expert_agent)
    workflow.add_node("interviewer", interviewer_agent)
    
    # Define Edges
    workflow.set_entry_point("extractor")
    
    # Conditional Edge from Extractor
    workflow.add_conditional_edges(
        "extractor",
        check_extraction_success,
        {
            "continue": "title",
            "end": END
        }
    )
    
    # Sequential Chain of Optimization Agents
    # Title -> Personal Info -> Skills -> Certificate -> Work Exp -> Education -> Projects -> Self Eval
    workflow.add_edge("title", "personal_info")
    workflow.add_edge("personal_info", "skills")
    workflow.add_edge("skills", "certificate")
    workflow.add_edge("certificate", "work_experience")
    workflow.add_edge("work_experience", "education")
    workflow.add_edge("education", "project_experience")
    workflow.add_edge("project_experience", "self_evaluation")
    
    # Assembly -> Layout -> Interview
    workflow.add_edge("self_evaluation", "assembler")
    workflow.add_edge("assembler", "layout_expert")
    workflow.add_edge("layout_expert", "interviewer")
    workflow.add_edge("interviewer", END)
    
    # Compile
    return workflow.compile()
