from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.agents.matcher import match_job_to_user


llm = ChatGroq(
    # model="llama-3.3-70b-versatile",
    model="openai/gpt-oss-120b",
    temperature=0.4,
    max_tokens=1500
)

# Per-type prompt templates. cover_letter/linkedin_message/upwork_proposal/
# cold_pitch are ported (tone, structure, word-count guidance, and
# placeholder conventions preserved) from what was previously a set of
# separate xAI/OpenRouter-backed Next.js API routes, now consolidated
# behind this one Groq-backed generator. resume_tailoring/interview_prep
# fall back to GENERIC_TEMPLATE - upgrading those to type-specific output
# (e.g. a genuinely restructured resume) is a deliberately separate,
# not-yet-scoped piece of work.

COVER_LETTER_TEMPLATE = ChatPromptTemplate.from_template(
    """
    You are an expert Executive Career Coach and ATS Specialist.
    Based on the provided job details and candidate fit analysis, write a highly optimized, persuasive, and world-class cover letter.
    Make sure it sounds natural, enthusiastic, professional, and directly aligns the candidate's achievements with the company's needs.
    Do not wrap the output in markdown code blocks. Just return the raw text format with clear paragraphs. Include placeholders like [Company Name] or [Hiring Manager] if you cannot infer them.

    **Job Title:** {job_title}
    **Full Job Description:** {job_description}

    **Candidate Fit Analysis:**
    {analysis}
    """
)

LINKEDIN_MESSAGE_TEMPLATE = ChatPromptTemplate.from_template(
    """
    You are an expert Career Coach and LinkedIn Networking Specialist.
    Based on the provided target job/person description and candidate fit analysis, write a highly optimized, engaging, and professional LinkedIn Direct Message or connection request note.
    Keep it extremely concise (aim for under 150-200 words total).
    Start with a warm, personalized greeting. Quickly mention a shared interest, mutual connection, or compliment their recent work/company to build rapport. Briefly highlight a specific, relevant achievement or skill from the candidate's background that aligns with the target. End with a low-pressure Call To Action (e.g., asking for a brief chat or their thoughts on a specific topic).
    Do not wrap the output in markdown code blocks. Just return the raw text format. Include placeholders like [Target Name] or [User Name] for the user to fill in if they cannot be inferred.

    Requirements:
    - Professional tone, but conversational.
    - Easy to read on mobile.
    - Focus on networking and relationship building, not just begging for a job.

    **Target Job / Person Description:** {job_title}
    {job_description}

    **Candidate Fit Analysis:**
    {analysis}
    """
)

UPWORK_PROPOSAL_TEMPLATE = ChatPromptTemplate.from_template(
    """
    You are an expert Freelance Success Coach and Upwork Proposal Specialist.
    Based on the provided Upwork job description and candidate fit analysis, write a highly optimized, persuasive, and winning Upwork proposal.
    Keep it concise, engaging, and professional.
    Start with a hook addressing the client's core problem, concisely highlight relevant past experience that proves capability, and end with a Call To Action or a thoughtful question to prompt a reply.
    Do not be overly formal. Avoid generic openings like "Dear Hiring Manager" (use "Hi there" or the client's name if inferable).
    Do not wrap the output in markdown code blocks. Just return the raw text format with clear paragraphs. Include placeholders like [Your Name] for the freelancer to fill in.

    **Upwork Job Title:** {job_title}
    **Upwork Job Description:** {job_description}

    **Candidate Fit Analysis:**
    {analysis}
    """
)

COLD_PITCH_TEMPLATE = ChatPromptTemplate.from_template(
    """
    You are an expert Sales Strategist and Freelance Consultant.
    Based on the provided target job/project/company description and candidate fit analysis, write a highly optimized, generic but completely tailored cold email or proposal pitch.
    It should not be platform specific (like Upwork or LinkedIn), but meant for an email, a generic job board, or a direct submission.
    Structure:
    1. Compelling subject line (if applicable, else just a strong hook).
    2. Strong opening that addresses a pain point.
    3. Brief mention of relevant value/wins based on the candidate's background.
    4. Clear and confident Call To Action.
    Do not wrap the output in markdown code blocks. Just return the raw text format. Include placeholders like [Client Name] for the user to fill in if they cannot be inferred.

    Requirements:
    - Persuasive, confident tone.
    - Not overly formal or dry.
    - Focus on the ROI and value the candidate can bring.

    **Target Job / Project / Company:** {job_title}
    {job_description}

    **Candidate Fit Analysis:**
    {analysis}
    """
)

GENERIC_TEMPLATE = ChatPromptTemplate.from_template(
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
    """
)

TYPE_SPECIFIC_TEMPLATES = {
    "cover_letter": COVER_LETTER_TEMPLATE,
    "linkedin_message": LINKEDIN_MESSAGE_TEMPLATE,
    "upwork_proposal": UPWORK_PROPOSAL_TEMPLATE,
    "cold_pitch": COLD_PITCH_TEMPLATE,
}


async def generate_application_package(
    user_id: str,
    job_description: str,
    job_title: str,
    application_type: str = "cover_letter",
    match_result: dict | None = None,
):
    """
    application_type: cover_letter, resume_tailoring, interview_prep,
    linkedin_message, upwork_proposal, cold_pitch
    """

    if match_result is None:
        match_result = await match_job_to_user(user_id, job_description, job_title)

    analysis = match_result["analysis"]

    prompt = TYPE_SPECIFIC_TEMPLATES.get(application_type, GENERIC_TEMPLATE)
    chain = prompt | llm

    result = await chain.ainvoke({
        "application_type": application_type.replace("_", " "),
        "job_title": job_title,
        "job_description": job_description,
        "analysis": str(analysis)
    })

    return {
        "application_package": application_type,
        "content": result.content,
        "match_score": analysis.match_score,
        "sources_used": match_result["sources_used"],
        "match_analysis": analysis.model_dump(),
    }
