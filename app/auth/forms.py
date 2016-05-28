from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(Form):
    email = StringField('邮件', validators = [Required(), Email()])
    password = PasswordField('密码', validators = [Required()])
    remember_me  =BooleanField('记住我')
    submit = SubmitField('注册')

class RegisterForm(Form):
    email = StringField('邮件', validators = [Required(), Email()])
    username = StringField('用户名', validators = [Required(), Length(1, 64), 
                            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 
                            '用户名必须由字母、下划线、数字、点号组成')])
    password = PasswordField('密码', validators = [Required(), Length(1, 16), 
                            EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('确认密码', validators = [Required()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email = field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')