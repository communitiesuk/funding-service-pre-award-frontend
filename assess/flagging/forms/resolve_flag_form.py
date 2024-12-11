from flask_wtf import FlaskForm
from wtforms import RadioField, TextAreaField
from wtforms.validators import InputRequired, length

from config import Config


class ResolveFlagForm(FlaskForm):
    resolution_flag = RadioField(
        "resolve",
        choices=["RESOLVED", "STOPPED"],
        validators=[InputRequired(message="Select a resolution")],
    )
    justification = TextAreaField(
        "justification",
        validators=[
            InputRequired(message="Provide a reason for resolving the flag"),
            length(max=Config.TEXT_AREA_INPUT_MAX_CHARACTERS),
        ],
    )
