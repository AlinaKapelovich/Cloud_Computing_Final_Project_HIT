"""Visit form (WTForms) used by the doctor to record a clinical encounter."""
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class VisitForm(FlaskForm):
    complaints = TextAreaField("Complaints", validators=[DataRequired(), Length(max=2000)])
    diagnosis = TextAreaField("Diagnosis", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Save visit & add prescription")
