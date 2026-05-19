from langchain_groq import ChatGroq
from llama_index.core import ChatPromptTemplate

from app.agents.matcher import match_job_to_user


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.4,
    max_tokens=1500
)

async def generate_application_package(user_id:str, job_description:str, job_title:str, application_type: str="cover_letter"):
    """
    application_type: cover_letter, upwork_proposal, linkedin_message
    """

    match_result = await match_job_to_user(user_id, job_description, job_title)
    analysis = match_result["analysis"]

    prompt = ChatPromptTemplate.from_tempate(
        """
        You are an expert career agent that generates tailored {application_type} for job applications based on a detailed analysis of the candidate's fit for the job.

        **Job Title:** {job_title}
        **Full Job Description:** {job_description}

        **Candidate Fit Analysis:**
        {analysis}

        Based on the above analysis, generate a highly tailored {application_type} that addresses the key tailoring recommendations and highlights the candidate's strong matches while mitigating any concerns or skill gaps. The {application_type} should be concise, impactful, and directly relevant to the job description and the candidate's background.

        Rules:
        - Use a professional and engaging tone.
        - Focus on the most relevant skills and experiences.
        - Address any potential concerns in a positive light.
        - Ensure the content is specific to the job description provided.
        - Make it natural and human-sounding
        - Heavily reference the candidate's real experience (use the analysis)
        - Keep it concise but compelling (300-450 words for cover letter)
        - Use achievements and metrics where possible
        - End with a strong call to action

        Return only the final document. No explanations or references to the analysis should be included in the output.
        """)
    chain = prompt | llm

    result = await chain.ainovoke({
        "application_type": application_type.replace("_", " "),
        "job_title": job_title,
        "analysis": str(analysis)
    })

    return {
        "application_package": application_type,
        "content": result.content,
        "match_score": analysis.match_score,
        "source_used": match_result["sources_count"]
    }