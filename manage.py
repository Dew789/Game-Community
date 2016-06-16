#!/usr/bin/env python
from app import create_app, db
from app.models import User, Role, Post, Comment, Game, Score, Recommend
from app.generate_recommend import insert_similar_items
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app('default')
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('database', MigrateCommand)

def make_shell_context():
    '''初始化app示例，以及模型函数'''
    return dict(app = app, db = db, User = User, Role = Role, 
                Post = Post, Comment = Comment, Game = Game, 
                Score = Score, Recommend = Recommend, insert_similar_items = insert_similar_items)
manager.add_command("shell", Shell(make_context = make_shell_context))

if __name__ == '__main__':
    manager.run()