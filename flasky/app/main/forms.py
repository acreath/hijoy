from flask_wtf import Form
from wtforms import StringField, SubmitField,TextAreaField,BooleanField,SelectField
from wtforms.validators import Required,Length,Regexp,Email
from flask_pagedown.fields import PageDownField 

class NameForm(Form):
    name = StringField('What is your name?',validators=[Required()])
    submit = SubmitField('Submit')

class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0, 64)]) 
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

#管理员使用的资料编辑器
class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[Required(), Length(1,64),
                            Email()])
    username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 
                                                'Usernames must have only letters, '
                                                'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs): 
        super(EditProfileAdminForm, self).__init__(*args, **kwargs) 
        self.role.choices = [(role.id, role.name)
                                  for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first(): 
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first(): 
            raise ValidationError('Username already in use.')

#博客文章表单
class PostForm(Form):
    body = PageDownField("what's on your mind?",validators=[Required()])
    submit = SubmitField("Submit")

#评论表单
class CommentForm(Form):
    body = StringField('',validators=[Required()])
    submit = SubmitField('Submit')