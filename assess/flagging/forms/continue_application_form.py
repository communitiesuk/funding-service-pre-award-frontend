from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import InputRequired, length

from config import Config


class ContinueApplicationForm(FlaskForm):
    reason = TextAreaField(
        "reason",
        validators=[
            length(max=Config.TEXT_AREA_INPUT_MAX_CHARACTERS),
            InputRequired(message="Provide a reason for continuing assessment"),
        ],
    )
