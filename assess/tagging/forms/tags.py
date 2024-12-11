from flask_wtf import FlaskForm
from wtforms import RadioField, SelectMultipleField, TextAreaField
from wtforms.validators import InputRequired, Regexp, length

from config import Config


class TagAssociationForm(FlaskForm):
    tags = SelectMultipleField(
        "Tags to associate",
        validators=[
            InputRequired(message="Provide which tag(s) you are associating"),
        ],
    )


tag_value_field = TextAreaField(
    "value",
    validators=[
        InputRequired(message="Provide a value for the tag."),
        length(max=Config.TEXT_AREA_INPUT_MAX_CHARACTERS),
        Regexp(r"^[A-Za-z0-9_' -]+$", message="Invalid characters in value."),
    ],
)


class NewTagForm(FlaskForm):
    value = tag_value_field

    type = RadioField(
        "type",
        validators=[InputRequired()],
    )


class EditTagForm(FlaskForm):
    value = tag_value_field


class DeactivateTagForm(FlaskForm):
    pass


class ReactivateTagForm(FlaskForm):
    pass
