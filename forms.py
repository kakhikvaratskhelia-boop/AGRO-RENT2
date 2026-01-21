from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo

class MachineForm(FlaskForm):
    name = StringField('Machine Name', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    price = FloatField('Price (GEL)', validators=[DataRequired()])
    submit = SubmitField('Confirm')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')