#!/usr/bin/env python
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

class Follow(db.Model):
    '''自定义用户关注关联表，使用两个一对多实现多对多'''
    __tablename__ = 'follows'

    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)
        


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

    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.Integer, unique = True, index = True)
    username = db.Column(db.String(64), unique = True, index = True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default = False)
    about_me = db.Column(db.Text())
    location = db.Column(db.String(64))
    avatar_big = db.Column(db.String(64), default = 'app/static/photo/ul.png')
    avatar_small = db.Column(db.String(64), default = 'app/static/photo/u.png')
    member_since = db.Column(db.DateTime(), default = datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default = datetime.utcnow)
    # 用户文章
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
    # 用户对文章的评论
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    # 用户关注的人
    followed = db.relationship('Follow', foreign_keys = [Follow.follower_id],
                                backref = db.backref('follower', lazy='joined'), 
                                lazy = 'dynamic', cascade = 'all, delete-orphan')
    # 关注用户的人      
    followers = db.relationship('Follow',foreign_keys = [Follow.followed_id],
                                backref = db.backref('followed', lazy='joined'),
                                lazy = 'dynamic',cascade = 'all, delete-orphan')

    # 对游戏的评分
    scores = db.relationship('Score', backref='gamer',lazy='dynamic',cascade='all, delete-orphan')

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

    def follow(self, user):
        '''关注用户'''
        if not self.is_following(user):
            f = Follow(follower = self, followed = user)
            db.session.add(f)

    def unfollow(self, user):
        '''解除关注'''
        f = self.followed.filter_by(followed_id = user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        '''是否关注'''
        return self.followed.filter_by(followed_id = user.id).first() is not None

    def is_followed_by(self, user):
        '''是否被关注'''
        return self.followers.filter_by(follower_id = user.id).first() is not None

    @property
    def followed_posts(self):
        '''返回用户关注者的文章'''
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    @staticmethod
    def generate_fake(count = 100):
        '''批量生成虚拟用户'''
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email = forgery_py.internet.email_address(),
                    username = forgery_py.internet.user_name(True),
                    password = forgery_py.lorem_ipsum.word(),
                    confirmed = True,
                    location = forgery_py.address.city(),
                    about_me = forgery_py.lorem_ipsum.sentence(),
                    member_since = forgery_py.date.date(True))
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
    # 文章的评论
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

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
        
# 设置文章监听器监，文章变化文章的markdown格式变化
db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    '''对文章的评论'''
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    disabled = db.Column(db.Boolean)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
# 设置评论监听器，评论变化markdown格式变化
db.event.listen(Comment.body, 'set', Comment.on_changed_body)

class Game(db.Model):
    """游戏信息"""
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key = True)
    name_ch = db.Column(db.String(128), unique = True)
    name_en = db.Column(db.String(128), unique = True)
    game_type = db.Column(db.String(64))
    producer = db.Column(db.String(64))
    publisher = db.Column(db.String(64))
    release_time = db.Column(db.Date)
    introduction = db.Column(db.Text)
    cover = db.Column(db.String(64))
    # 游戏评分
    scores = db.relationship('Score', backref='game', lazy='dynamic',cascade='all, delete-orphan')
    # 与其相似的游戏
    similar_games = db.relationship('Recommend', backref='prim_game', lazy='dynamic',cascade='all, delete-orphan')

    @property
    def get_recommend(self):
        return Game.query.join(Recommend, Recommend.rel_game_id == Game.id).\
                filter(Recommend.prim_game_id == self.id).all()

    @staticmethod
    def insert_games(count = 10):
        '''向游戏库中添加游戏'''
        from urllib import request
        from bs4 import BeautifulSoup

        def insert_game(url):
            '''抓取游民星空的游戏信息'''
            html = request.urlopen(url).read()
            soup = BeautifulSoup(html, 'html.parser')
            games = soup.select('.R')
            for game in games:
                # 抓取游戏简介
                detail = game.select('.R_1')[0].a['href']
                html = request.urlopen(detail).read()
                soup = BeautifulSoup(html, 'html.parser')
                brief = game.select('.R2_1')
                # 解决时间格式不统一问题
                try:
                    release_time = datetime.strptime(brief[5].span.string, '%Y.%m.%d')
                except:
                    release_time = None
                g = Game(name_ch = brief[0].a.string,
                         name_en = brief[1].span.string,
                         game_type = brief[2].span.string,
                         introduction = soup.select('.YXJS')[0].p.string,
                         cover = game.select('.R_1')[0].img['src'],
                         producer = brief[3].span.string,
                         publisher = brief[4].span.string,
                         release_time = release_time)
                db.session.add(g)
                db.session.commit()

        insert_game('http://ku.gamersky.com/sp/0-0-0-0-30-0.html')
        i = 2
        while i <= count:
            url = 'http://ku.gamersky.com/sp/0-0-0-0-30-0_{}.html'.format(i)
            i += 1
            insert_game(url)

class Score(db.Model):
    '''对游戏的评分'''
    __tablename__ = 'scores'

    score = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), primary_key = True)

    @staticmethod
    def generate_fake():
        '''生成随机评分用于测试推荐系统'''
        from random import seed, randint, randrange
        from sqlalchemy.exc import IntegrityError

        seed()
        for user_id in range(1, 103):
            for i in range(50):
                game_id = randint(1, 160)
                score = randrange(2, 12, 2)
                
                s = Score(user_id = user_id,
                             game_id = game_id,
                             score = score)
                db.session.add(s)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

class Recommend(db.Model):
    '''游戏之间基于距离的相似度评价'''
    __tablename__ = 'recommends'

    prim_game_id = db.Column(db.Integer, db.ForeignKey('games.id'), primary_key = True)
    rel_game_id = db.Column(db.Integer, db.ForeignKey('games.id'), primary_key = True)
    correlation = db.Column(db.Float)
