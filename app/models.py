from flask.ext.login import UserMixin, AnonymousUserMixin
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from datetime import datetime
from markdown import markdown
import bleach

@login_manager.user_loader
def load_user(user_id):
    '''用户回掉函数，接受Unicode形式的用户标示符，如果找到用户，
        返回用户对象，否则返回None
    '''
    return User.query.get(int(user_id))

class Permission(object):
    '''
    定义程序的权限
    1.关注用户 0b00000001
    2.发表评论 0b00000010
    3.写文章 0b00000100
    4.管理他人评论 0b00001000
    5.网站管理 0b10000000
    '''
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80
        


class Role(db.Model):
    '''
    定义角色模型，表明用户的身份
    1.匿名用户：未登录只有阅读权限 0b000000
    2.用户，拥有发布文章、发表评论、关注用户这是默认的角色 0b00000111
    3.协管员，具有审查不当评论的权限 0b00001111
    3.管理员，具有所有权限0b11111111
    '''
    @staticmethod
    def insert_roles():
        '''自动添加角色名，并赋予权限'''
        roles = {
            'User' : (Permission.FOLLOW |
                      Permission.COMMENT |
                      Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
            }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
                role.permissions = roles[r][0]
                role.default = roles[r][1]
                db.session.add(role)
                db.session.commit()

    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default = False, index = True)
    users = db.relationship('User', backref = 'role')
    permissions = db.Column(db.Integer)

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
    about_me = db.Column(db.Text())
    location = db.Column(db.String(64))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow) 
    # 与专栏文章的一对多关系 
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')

    def __init__(self, **kwargs):
        ''' 调用db.Model的构造函数，如果不存在角色名根据情况赋予'''
        super(User, self).__init__(**kwargs)

        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()

    def can(self, permissions):
        '''判断角色的权限'''
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        '''判断角色是否为管理员'''
        return self.can(Permission.ADMINISTER)
            

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

    def generate_change_email_token(self, new_email, expiration=3600):
        ''' 生成用户修改邮箱时的安全令牌'''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email' : new_email})

    def change_email(self, token):
        '''检验用户重修改邮箱邮件的安全令牌是否正确，如果正确将新密码存入数据库'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        self.email = data.get('new_email')
        db.session.add(self)
        return True

    def ping(self):
        '''刷新用户最后登录时间'''
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @staticmethod
    def generate_fake(count = 100):
        '''批量生成虚拟用户'''
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email = forgery_py.internet.email_address(),
                    username=forgery_py.internet.user_name(True),
                    password=forgery_py.lorem_ipsum.word(),
                    confirmed=True,
                    location=forgery_py.address.city(),
                    about_me=forgery_py.lorem_ipsum.sentence(),
                    member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<User %r>' % self.username



class AnonymousUser(AnonymousUserMixin):
    '''定义匿名类，使current_user不论在用户是否登陆的情况下都可以查询权限'''
    def can(self, permissions):
        return False
    def is_administrator(self):
        return False
login_manager.anonymous_user = AnonymousUser

class Post(db.Model):
    '''定于用户专栏文章模型'''
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)

    @staticmethod
    def generate_fake(count = 100):
        '''批量生成虚拟文章'''
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body = forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                    timestamp = forgery_py.date.date(True),
                    author = u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        '''将markdown文本转换为html格式'''
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format = 'html'),
            tags = allowed_tags, strip = True))
        
# 设置sqlalchemy监听时间
db.event.listen(Post.body, 'set', Post.on_changed_body)