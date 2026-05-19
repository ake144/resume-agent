from typing import TypedDict


class ApplicationState(TypedDict):
    user_id: str
    job_description: str
    job_title: str
    application:str
    match_analysis: dict
    final_output: dict
