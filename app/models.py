from . import db

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

class User(db.Model):
    '''
    定义用户模型，储存用户资料
    '''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username