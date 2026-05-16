from langchain_groq import ChatGroq
from llama_index.core import ChatPromptTemplate

from app.rag.retriever import retrieve_relevant_resumes


llm = ChatGroq(
    model="llama-3.3-70b-versatile",   # Strong reasoning + free tier
    temperature=0.3,
    max_tokens=1024
)

async def match_job_to_user(user_id:str, job_description:str, job_title:str):

    context_docs = await retrieve_relevant_resumes(
        query=job_description,
        user_id=user_id,
        top_k=5
    )

    context_text = "\n\n".join([
        f"Source: {doc.metadata.get("document_type", "unknown")} - {doc.metadata.get("title", "no title")}\n{doc.page_content}"
        for doc in context_docs
    ])

    prompt  = ChatPromptTemplate.from_template("""
             You are an expert career coach. Analyze how well the candidate matches this job.

                **Job Title:** {job_title}
                **Job Description:** {job_description}

                **Candidate's Relevant Experience:**
                {context_text}

                Provide a detailed analysis with:
                1. Match Score (0-100)
                2. Strong Matches (with specific citations from candidate's data)
                3. Potential Concerns / Skill Gaps
                4. Key Tailoring Recommendations

                Be honest, constructive, and always ground your answer in the provided context.
                Do not hallucinate experience.
    """)       

    chain = prompt | llm

    response = await chain.ainvoke({
        "job_title": job_title,
        "job_description": job_description,
        "context_text": context_text or "No relevant experience found in the candidate's data."
    })
    return {
        "analysis": response.content,
        "match_score": extract_score(response.content),  # Placeholder - can be extracted from response if structured output is implemented
        "Sources_used": len(context_docs)
    }                            
                                               
     
