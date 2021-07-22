"""WTForms classes for html forms"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class UserEditForm(FlaskForm):
    """Edit user profile form."""

    username = StringField('Username')
    email = StringField('E-mail', validators=[Optional(), Email()])
    image_url = StringField('Image URL')
    header_image_url = StringField('Header Image URL')
    bio = TextAreaField('Bio')
    password = PasswordField('Password', validators=[Length(min=6)])


class TokenValidationForm(FlaskForm):
	"""CSRF protection"""
