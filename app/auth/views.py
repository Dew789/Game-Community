from flask import render_template, redirect, url_for, flash, request
from flask.ext.login import login_user, logout_user, login_required, current_user
from . import auth
from ..models import User
from flask.ext.login import login_user
from .forms import LoginForm, RegisterForm, ChangePassword, PasswordResetRequestForm, PasswordResetForm
from .. import db
from ..email import send_email


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
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('错误的用户名或密码')
    return render_template('auth/login.html', form = form)


@auth.route('/logout')
@login_required
def logout():
    '''
    用户登出函数，登出用户，并返回主页面
    '''
    logout_user()
    flash('你已经退出了')
    return redirect(url_for('main.index'))
    

@auth.route('/register', methods=['GET', 'POST'])
def register():
    '''
    注册函数，注册用户，并向用户邮箱中发送确认邮件
    '''
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email = form.email.data,
                    username = form.username.data,
                    password = form.password.data)
        db.session.add(user)
        db.session.commit()
        # 生成安全邮件地址
        token = user.generate_confirmation_token()
        send_email(user.email, '请确认你的账户','auth/email/confirm', user=user, token=token)
        flash('一封确认邮件已经发送到了你的邮箱')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form = form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('您已经确认了你的邮件，欢迎')
    else:
        flash('您的邮件无效或过期')
    return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    '''
    满足以下条件before_request()函数会拦截request请求
    1.用户已经登陆，且没有通过邮件进行认证
    2.用户请求的路由不是'auth'端点，不是静态文件
    '''
    if current_user.is_authenticated and not current_user.confirmed \
            and request.endpoint[:5] != 'auth.'and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    '''判断用户是否通过确认，没有用过确认返回提示激活页面'''
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    '''在用户未激活且以登陆的情况下重新发送确认邮件'''
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '请确认你的账户','auth/email/confirm', user=current_user, token=token)
    flash('一封新的确认邮件已经发送到了你的邮箱')
    return redirect(url_for('main.index'))


@auth.route('/change_password', methods = ['GET', 'POST'])
@login_required
def change_password():
    '''修改函数，在用户提交原密码后可以修改密码'''
    form = ChangePassword()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            flash('密码已经修改')
            return redirect(url_for('main.index'))
        else:
            flash('密码不正确')
    return render_template('auth/change_password.html', form = form)

@auth.route('/reset', methods = ['GET', 'POST'])
def password_reset_request():
    ''' 如果用户忘记密码，输入正确邮件地址后会收到一封确认密码邮件'''
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is None:
            flash('邮箱不存在')
        else:
            token = user.generate_reset_token()
            send_email(user.email, '请修改您的密码','auth/email/reset_password', user = user, token = token)
            flash('一封确认邮件已经发送到了你的邮箱')
        redirect(url_for('auth.password_reset_request'))
    return render_template('auth/reset_passowrd.html', form = form)


@auth.route('/reset/<token>', methods = ['GET', 'POST'])
def password_reset(token):
    '''用户输入新密码,并重置'''
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('你的密码已经重置')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_passowrd.html', form = form)