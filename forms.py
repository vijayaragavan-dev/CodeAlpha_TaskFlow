import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional

from models import fetch_one


class BaseForm(FlaskForm):
    pass


class RegistrationForm(BaseForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=50, message='Username must be 3-50 characters')
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message='Enter a valid email address'),
            Length(max=100)
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters')
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = fetch_one(
            'SELECT id FROM users WHERE username=%s',
            (username.data.strip(),)
        )
        if user:
            raise ValidationError('Username already exists')

    def validate_email(self, email):
        user = fetch_one(
            'SELECT id FROM users WHERE email=%s',
            (email.data.strip(),)
        )
        if user:
            raise ValidationError('Email already registered')

    def validate_password(self, password):
        val = password.data
        if not re.search(r'[A-Z]', val):
            raise ValidationError('Password must include an uppercase letter')
        if not re.search(r'[a-z]', val):
            raise ValidationError('Password must include a lowercase letter')
        if not re.search(r'[0-9]', val):
            raise ValidationError('Password must include a digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-]', val):
            raise ValidationError('Password must include a special character')


class LoginForm(BaseForm):
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message='Enter a valid email address')
        ]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class MemberForm(BaseForm):
    username_or_email = StringField(
        'Username or Email',
        validators=[DataRequired(message='Enter a username or email')]
    )
    submit = SubmitField('Add Member')


class TaskForm(BaseForm):
    title = StringField(
        'Title',
        validators=[
            DataRequired(message='Title is required'),
            Length(min=3, max=200, message='Title must be 3-200 characters')
        ]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=5000)]
    )
    assigned_to = SelectField(
        'Assign To',
        coerce=int,
        validators=[Optional()]
    )
    priority = SelectField(
        'Priority',
        choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')],
        default='Medium'
    )
    status = SelectField(
        'Status',
        choices=[('To Do', 'To Do'), ('In Progress', 'In Progress'), ('Completed', 'Completed')],
        default='To Do'
    )
    deadline = DateField('Deadline', validators=[Optional()])
    submit = SubmitField('Save Task')


class CommentForm(BaseForm):
    comment = TextAreaField(
        'Comment',
        validators=[
            DataRequired(message='Comment cannot be empty'),
            Length(max=1000, message='Comment must be under 1000 characters')
        ],
        render_kw={'rows': 3, 'placeholder': 'Write a comment...'}
    )
    submit = SubmitField('Add Comment')


class ProjectForm(BaseForm):
    name = StringField(
        'Project Name',
        validators=[
            DataRequired(message='Project name is required'),
            Length(min=3, max=150, message='Project name must be 3-150 characters')
        ]
    )
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=1000, message='Description must be under 1000 characters')
        ]
    )
    submit = SubmitField('Save Project')
