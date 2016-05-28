from flask.ext.login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    '''用户回掉函数，接受Unicode形式的用户标示符，如果找到用户，
        返回用户对象，否则返回None
    '''
    return User.query.get(int(user_id))


class Role(db.Model):
    '''
    定义角色模型，表明用户的身份
    '''
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model, UserMixin):
    '''
    定义用户模型，储存用户资料
    '''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Integer, unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    @property
    # 密码不可读
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    # 密码加密， 生成密码散列
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
    #验证密码是否正确，返回布尔值
        return check_password_hash(self.password_hash, password)
    

    def __repr__(self):
        return '<User %r>' % self.username

