from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.core.config import settings
from app.models.jobMatch import JobMatchAnalysis
from app.rag.retriever import retrieve_relevant_resumes


llm = ChatGroq(
    # model="llama-3.3-70b-versatile",   # Strong reasoning + free tier
    model="openai/gpt-oss-120b",
    temperature=0.3,
    max_tokens=1200
)

parser = PydanticOutputParser(pydantic_object=JobMatchAnalysis)


def find_preference_conflicts(
    job_title: str,
    job_description: str,
    preferences: dict | None,
) -> list[str]:
    """Find explicit conflicts without guessing when a job omits a detail."""
    if not preferences:
        return []

    text = f"{job_title} {job_description}".lower()
    conflicts: list[str] = []
    work_modes = {mode.lower() for mode in (preferences.get("work_modes") or [])}
    if "remote" in work_modes and any(
        phrase in text for phrase in ("on-site", "onsite", "in office", "office-based")
    ):
        conflicts.append("Saved preference requires remote work, but the posting indicates onsite work.")
    if preferences.get("visa_sponsorship_required") and any(
        phrase in text
        for phrase in (
            "no visa sponsorship",
            "do not provide visa sponsorship",
            "without sponsorship",
            "must have work authorization",
        )
    ):
        conflicts.append("Visa sponsorship is required, but the posting appears not to provide it.")
    return conflicts


async def match_job_to_user(
    user_id: str,
    job_description: str,
    job_title: str,
    preferences: dict | None = None,
    target_roles: list[str] | None = None,
):
    
    context_docs = await retrieve_relevant_resumes(
        query=job_description,
        user_id=user_id,
        top_k=settings.retrieval_top_k,
        include_jobs=settings.retrieval_include_jobs,
    )

    context_text = "\n\n".join([
        f"Source: {doc.metadata.get('document_type', 'unknown')} - {doc.metadata.get('title', 'no title')}\n{doc.page_content}"
        for doc in context_docs
    ])

    prompt  = ChatPromptTemplate.from_template("""
            You are an expert, honest career matching agent.

            **Job Title:** {job_title}
            **Full Job Description:** {job_description}

            **Candidate's Saved Preferences:** {preferences_text}
            **Target Roles:** {target_roles_text}

            **Candidate's Background (Only use this information):**
            {context_text}

            {format_instructions}

            Rules:
            - Only use information present in the Candidate's Background.
            - Be critical and realistic.
            - Always cite which document the point comes from.
            - Treat explicit saved preference conflicts as blockers, not as missing skills.
            """)    

    chain = prompt | llm

    response = await chain.ainvoke({
        "job_title": job_title,
        "job_description": job_description,
        "context_text": context_text or "No relevant experience found in the candidate's data.",
        "preferences_text": str(preferences or "No saved preferences"),
        "target_roles_text": ", ".join(target_roles or []) or "No target roles saved",
        "format_instructions": parser.get_format_instructions()
    })
    parsed_analysis = parser.parse(response.content)
    conflicts = find_preference_conflicts(job_title, job_description, preferences)
    parsed_analysis.hard_constraints = conflicts
    parsed_analysis.preference_alignment = "Blocked" if conflicts else "No explicit conflict found"
    return {
        "analysis": parsed_analysis,
        "sources":[
            {
                "type": doc.metadata.get("document_type", "unknown"),
                "title": doc.metadata.get("title", "no title"), 
            } for doc in context_docs
        ],  
        "sources_used": len(context_docs)
    }                            
                                               
     
