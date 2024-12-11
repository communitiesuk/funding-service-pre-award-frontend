from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import InputRequired, length

from config import Config


class CommentsForm(FlaskForm):
    comment = TextAreaField(
        "Comment",
        validators=[
            length(max=Config.TEXT_AREA_INPUT_MAX_CHARACTERS),
            InputRequired(),
        ],
    )
