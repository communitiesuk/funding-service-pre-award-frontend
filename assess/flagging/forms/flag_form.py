from flask_wtf import FlaskForm
from wtforms import RadioField, SelectMultipleField, TextAreaField
from wtforms.validators import InputRequired, length

from config import Config


class FlagApplicationForm(FlaskForm):
    justification = TextAreaField(
        "Reason for flagging",
        validators=[
            length(max=Config.TEXT_AREA_INPUT_MAX_CHARACTERS),
            InputRequired(message="Provide a justification for flagging this application"),
        ],
    )
    section = SelectMultipleField(
        "Sections to flag",
        choices=None,
        validators=[
            length(max=Config.TEXT_AREA_INPUT_MAX_CHARACTERS),
            InputRequired(message="Provide which section(s) you are flagging"),
        ],
    )

    teams_available = RadioField(
        "teams_available",
        choices=None,
        validators=[InputRequired(message="Select which team the flag should be allocated to")],
    )

    def __init__(self, section_choices=None, team_choices=None):
        super().__init__()
        self.section.choices = section_choices
        self.teams_available.choices = team_choices
        if not team_choices:
            self.teams_available.validators = []
            self.teams_available.validate_choice = False
