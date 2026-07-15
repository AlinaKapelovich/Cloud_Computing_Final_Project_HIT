"""Patient forms (WTForms) used by the Admin to create and edit patient records."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, DateField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class PatientForm(FlaskForm):
    national_id = StringField("National ID", validators=[DataRequired(), Length(min=3, max=32)])
    first_name = StringField("First name", validators=[DataRequired(), Length(max=60)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=60)])
    gender = SelectField(
        "Gender",
        choices=[("female", "Female"), ("male", "Male"), ("other", "Other")],
        validators=[DataRequired()],
    )
    pregnancy_status = BooleanField("Currently pregnant", validators=[Optional()])
    lactation_status = BooleanField("Currently lactating", validators=[Optional()])
    birth_date = DateField("Birth date", validators=[DataRequired()])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=32)])
    photo = FileField(
        "Photo",
        validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], "Images only.")],
    )
    submit = SubmitField("Save patient")
