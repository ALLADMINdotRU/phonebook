from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, MultipleFileField
from wtforms.validators import DataRequired, Email

class SendEmailForm(FlaskForm):
    to_email = StringField('Кому', validators=[DataRequired(), Email()])
    subject = StringField('Тема', validators=[DataRequired()])
    body = TextAreaField('Текст письма', validators=[DataRequired()])
    # attachments = MultipleFileField('Вложения')  # Пока оставим простую версию

