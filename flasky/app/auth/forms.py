from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from ..models import User
from wtforms import ValidationError

#用户登录表单
class LoginForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remenber_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

#用户注册表单
class RegistrationForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                                Email()])
    username = StringField('username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9]*$',0,'Usernames must have only letters, '
'numbers, dots or underscores')])
    password = PasswordField('Password', validators=[Required(), EqualTo('password2',message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

#用户修改密码的表单
class ChangepasswordForm(Form):
    old_password = PasswordField('Old Password', validators=[Required()])
    new_password = PasswordField('New_Password', validators=[Required(),EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm new password',
                              validators=[Required()])
    submit = SubmitField('submit')
   

#用户重设密码表单1:填写邮箱
class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                                Email()])
                                
    submit = SubmitField('Submit')

#用户输入新密码的表单
class ResetPasswordForm(Form):
    new_password = PasswordField('New Password', validators=[Required(),EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm Password', validators=[Required()])
    submit = SubmitField('Submit')