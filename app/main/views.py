from flask import render_template, flash, redirect, url_for, abort
from . import main
from ..models import User, Role
from .form import EditProfileForm, EditProfileAdminForm, FindUserForm
from flask.ext.login import login_required, current_user
from .. import db
from ..decorators import admin_required

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/user/<username>')
def user(username):
    '''用户资料页面'''
    user = User.query.filter_by(username = username).first()
    if user is None:
        abort(404)
    return render_template('user.html', user = user)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    '''普通用户编辑用户资料'''
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('你的信息已更新')
        return redirect(url_for('main.user', username = current_user.username))

    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form = form)

@main.route('/finduser', methods = ['GET', 'POST'])
@login_required
@admin_required
def find_profile_admin():
    '''管理员查找要修改的用户'''
    form = FindUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user:
            return redirect(url_for('main.eidit_profile_admin', username = form.username.data))
        flash('没有该用户')
    return render_template('find_user.html', form = form)

@main.route('/edit-profile/<username>', methods = ['GET', 'POST'])
@login_required
@admin_required
def eidit_profile_admin(username):
    '''管理员修改用户资料'''
    user = User.query.filter_by(username = username).first()
    form = EditProfileAdminForm(user = user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('用户信息已经被更新.')
        return redirect(url_for('main.user', username = user.username))

    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form = form)