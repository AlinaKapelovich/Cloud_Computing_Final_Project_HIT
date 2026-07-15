"""Upload form (WTForms) for handwritten prescription images."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Optional


class UploadPrescriptionForm(FlaskForm):
    national_id = StringField("Patient national ID (optional)", validators=[Optional(), Length(max=32)])
    image = FileField(
        "Prescription image",
        validators=[
            FileRequired(),
            FileAllowed(["png", "jpg", "jpeg", "gif", "webp", "bmp", "pdf"], "Images or PDF only."),
        ],
    )
    submit = SubmitField("Upload, validate & run OCR")
