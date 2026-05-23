from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.agents.generator import generate_application_package
from app.agents.matcher import match_job_to_user
from app.core.memory import add_to_memory
from app.models.workflow import ApplicationState


async def match_nodes(state:ApplicationState):
    analysis = await match_job_to_user(
        state['user_id'],
        state['job_description'],
        state['job_title']
    )

    await add_to_memory(state['user_id'], f"Analyzed job: {state['job_title']}", role="assistant")
    
    return {"match_analysis": analysis}


async def generate_node(state:ApplicationState):

    application_package = await generate_application_package(
        state['user_id'],
        state['job_description'],
        state['job_title'],
        "cover_letter"
    )
    return {"application": application_package["content"], "final_output": application_package}
async def critic_node(state: ApplicationState):
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=800
    )
    prompt = f"""
        Review this cover letter for the job: {state['job_title']}

        Match Score: {state['match_analysis']['analysis'].match_score}
        Cover Letter: {state['application']}

        Give constructive criticism and suggest improvements.
        """
    critique = await llm.ainvoke(prompt)

    return {"critique": critique.content}
     

def build_application_graph():
    workflow = StateGraph(ApplicationState)

    workflow.add_node("match", match_nodes)
    workflow.add_node("generate", generate_node)
    workflow.add_node("critique", critic_node)

    workflow.set_entry_point("match")
    workflow.add_edge("match", "generate")
    workflow.add_edge("generate", "critique")
    workflow.add_edge("critique", END)  # Allow going back to matching if user wants to tweak input settings
    
    return workflow.compile()

app_graph = build_application_graph()