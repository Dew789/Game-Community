#!/usr/bin/env python
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(Form):
    '''登陆表单'''
    email = StringField('邮件', validators = [Required(), Email()])
    password = PasswordField('密码', validators = [Required()])
    remember_me  =BooleanField('记住我')
    submit = SubmitField('登陆')

class RegisterForm(Form):
    ''' 注册表单'''
    email = StringField('邮件', validators = [Required(), Email()])
    username = StringField('用户名', validators = [Required(), Length(1, 64), 
                            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 
                            '用户名只能由字母、下划线、数字、点号组成')])
    password = PasswordField('密码', validators = [Required(), Length(8, 16), 
                            EqualTo('password2', message='密码输入不一致')])
    password2 = PasswordField('确认密码', validators = [Required()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        '''自定义验证函数，确保邮件唯一'''
        if User.query.filter_by(email = field.data).first():
            raise ValidationError('邮箱已经被注册过了')

    def validate_username(self, field):
        '''自定义验证函数，确保用户名唯一'''
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已经被使用')

class ChangePassword(Form):
    '''修改密码表单'''
    password = PasswordField('原密码', validators = [Required()])
    new_password = PasswordField('新密码', validators = [Required(), Length(1, 16), 
                            EqualTo('new_password2', message='密码不匹配')])
    new_password2 = PasswordField('确认密码', validators = [Required()])
    submit = SubmitField('提交')

class PasswordResetRequestForm(Form):
    """重设密码确认表单，用户会收到填写邮箱中的邮件"""
    email = StringField('请输入你的邮箱', validators = [Required(), Email()])
    submit = SubmitField('提交')

class PasswordResetForm(Form):
    """重置密码表单"""
    email = StringField('请输入你的邮箱', validators = [Required(), Email()])
    password = PasswordField('新密码', validators = [Required(), Length(1, 16), 
                            EqualTo('password2', message='密码不匹配')])
    password2 = PasswordField('确认密码', validators = [Required()])
    submit = SubmitField('提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('此邮箱未注册')

class EmailResetForm(Form):
    """修改邮箱地址表单"""
    password = PasswordField('您的密码', validators = [Required()])
    email = StringField('请输入新邮箱', validators = [Required(), Email()])
    submit = SubmitField('提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('此邮箱已经被注册')

            