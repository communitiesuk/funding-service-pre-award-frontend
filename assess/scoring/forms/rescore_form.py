from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms.validators import DataRequired


class RescoreForm(FlaskForm):
    """
    Given class is a form class model used to display
    the score form if a sub-criteria has already been
    rescored.
    """

    hidden = HiddenField("Hidden", validators=[DataRequired()])
