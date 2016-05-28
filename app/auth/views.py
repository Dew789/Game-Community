from flask import render_template, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, login_required
from . import auth
from ..models import User
from flask.ext.login import login_user
from .forms import LoginForm, RegisterForm
from .. import db


@auth.route('/login', methods=['GET', 'POST'])
def login():
    '''
    登陆函数，如果用户存在且密码正确，登陆用户
    否则弹出错误信息
    '''
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            # 记住用户登陆状态如果'记住我' 为True，则将数据保存在cookie
            login_user(user, form.remember_me.data)
            return redirect(url_for('main.index'))
        flash('错误的用户名或密码')
    return render_template('auth/login.html', form = form)


@auth.route('/logout')
@login_required
def logout():
    '''
    用户登出
    '''
    logout_user()
    flash('你已经退出了')
    return redirect(url_for('main.index'))
    

@auth.route('/register', methods=['GET', 'POST'])
def register():
    '''
    注册函数
    '''
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email = form.email.data,
                    username = form.username.data,
                    password = form.password.data)
        db.session.add(user)
        flash('恭喜你，现在可以登陆了')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form = form)