import inspect
from dataclasses import dataclass
from typing import List

from .application import Application


@dataclass
class FeedbackSurveyConfig:
    has_feedback_survey: bool = False
    is_feedback_survey_optional: bool = True
    has_section_feedback: bool = False
    is_section_feedback_optional: bool = True

    @staticmethod
    def from_json(d: dict):
        # Filter unknown fields from JSON dictionary
        return FeedbackSurveyConfig(
            **{k: v for k, v in d.items() if k in inspect.signature(FeedbackSurveyConfig).parameters}
        )


@dataclass
class Round:
    id: str
    assessment_start: str
    assessment_deadline: str
    deadline: str
    fund_id: str
    opens: str
    title: str
    short_name: str
    guidance_url: str = ""
    all_uploaded_documents_section_available: bool = False
    application_fields_download_available: bool = False
    display_logo_on_pdf_exports: bool = False
    is_expression_of_interest: bool = False
    applications: List[Application] = None
    feedback_survey_config: FeedbackSurveyConfig = None

    def __post_init__(self):
        if isinstance(self.feedback_survey_config, dict):
            self.feedback_survey_config = FeedbackSurveyConfig.from_json(self.feedback_survey_config)
        elif self.feedback_survey_config is None:
            self.feedback_survey_config = FeedbackSurveyConfig()

    @classmethod
    def from_dict(cls, d: dict):
        # Filter unknown fields from JSON dictionary
        return cls(**{k: v for k, v in d.items() if k in inspect.signature(cls).parameters})

    @staticmethod
    def from_json(data: dict):
        return Round(
            title=data.get("title"),
            id=data.get("id"),
            assessment_start=data.get("assessment_start"),
            assessment_deadline=data.get("assessment_deadline"),
            fund_id=data.get("fund_id"),
            opens=data.get("opens"),
            deadline=data.get("deadline"),
            guidance_url=data.get("guidance_url"),
            all_uploaded_documents_section_available=data.get("all_uploaded_documents_section_available") or False,
            application_fields_download_available=data.get("application_fields_download_available") or False,
            display_logo_on_pdf_exports=data.get("display_logo_on_pdf_exports") or False,
            feedback_survey_config=data.get("feedback_survey_config") or FeedbackSurveyConfig(),
            is_expression_of_interest=data.get("is_expression_of_interest") or False,
        )
