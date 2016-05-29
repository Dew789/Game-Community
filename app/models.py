from flask.ext.login import UserMixin
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
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
    '''用户模型'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Integer, unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        '''设置密码，密码的值为密码的散列值'''
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        '''验证密码的闪散值是否正确是否正确'''
        return check_password_hash(self.password_hash, password)



    def generate_confirmation_token(self, expiration=3600):
        ''' 生成用户注册确认邮件的加密令牌'''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
        
    def confirm(self, token):
        '''检验用户注册的确认邮件是否正确，如果正确设置confirmed为True'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True


    def generate_reset_token(self, expiration=3600):
        ''' 生成用户重设密码时的安全令牌'''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        '''检验用户重设密码邮件的安全令牌是否正确，如果正确将新密码存入数据库'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True
    

    def __repr__(self):
        return '<User %r>' % self.username

