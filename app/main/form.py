from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from flask.ext.pagedown.fields import PageDownField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import Role, User

class EditProfileForm(Form):
    '''普通用户资料管理表单'''
    location = StringField('居住地', validators=[Length(0, 64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')

class EditProfileAdminForm(Form):
    '''管理员修改用户资料表单'''
    email = StringField('邮件', validators=[Required(), Email()])
    username = StringField('用户名', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, \
                           '用户名只能包含字母、数字、点号、下划线')])
    confirmed = BooleanField('是否邮件确认')
    role = SelectField('角色', coerce=int)
    location = StringField('居住地', validators=[Length(0, 64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        # 集成基类的属性
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经被使用')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名被使用')

class FindUserForm(Form):
    """输入用户名或邮箱来找到用户"""
    username = StringField('用户名')
    find = SubmitField('查找')

    
class PostForm(Form):
    '''专栏文章表单类'''
    body = PageDownField("请写下你的想法吧", validators=[Required()])
    submit = SubmitField('提交')