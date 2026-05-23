from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.models.jobMatch import JobMatchAnalysis
from app.rag.retriever import retrieve_relevant_resumes


llm = ChatGroq(
    model="llama-3.3-70b-versatile",   # Strong reasoning + free tier
    temperature=0.3,
    max_tokens=1200
)

parser = PydanticOutputParser(pydantic_object=JobMatchAnalysis)
    
async def match_job_to_user(user_id:str, job_description:str, job_title:str):
    
    context_docs = await retrieve_relevant_resumes(
        query=job_description,
        user_id=user_id,
        top_k=12
    )

    context_text = "\n\n".join([
        f"Source: {doc.metadata.get('document_type', 'unknown')} - {doc.metadata.get('title', 'no title')}\n{doc.page_content}"
        for doc in context_docs
    ])

    prompt  = ChatPromptTemplate.from_template("""
            You are an expert, honest career matching agent.

            **Job Title:** {job_title}
            **Full Job Description:** {job_description}

            **Candidate's Background (Only use this information):**
            {context_text}

            {format_instructions}

            Rules:
            - Only use information present in the Candidate's Background.
            - Be critical and realistic.
            - Always cite which document the point comes from.
            """)    

    chain = prompt | llm

    response = await chain.ainvoke({
        "job_title": job_title,
        "job_description": job_description,
        "context_text": context_text or "No relevant experience found in the candidate's data.",
        "format_instructions": parser.get_format_instructions()
    })
    parsed_analysis = parser.parse(response.content)
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
                                               
     
