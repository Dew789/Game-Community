from flask import render_template, flash, redirect, url_for, abort, request, current_app, make_response
from . import main
from ..models import User, Role, Permission, Post
from .form import EditProfileForm, EditProfileAdminForm, FindUserForm, PostForm
from flask.ext.login import login_required, current_user
from .. import db
from ..decorators import admin_required, permission_required

@main.route('/')
def index():
    page = request.args.get('page', 1, type = int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page = current_app.config['POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('index.html', posts = posts,
                           show_followed = show_followed, pagination = pagination)

@main.route('/all')
@login_required
def show_all():
    '''设置显示用户所有文章'''
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show_followed', '', max_age = 30*24*60*60)
    return resp
    
@main.route('/followed')
@login_required
def show_followed():
    '''显示用户所关注的文章'''
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show_followed', '1', max_age = 30*24*60*60)
    return resp

@main.route('/user/<username>')
def user(username):
    '''用户资料页面'''
    user = User.query.filter_by(username = username).first()
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type = int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
                  page, per_page = current_app.config['POSTS_PER_PAGE'], error_out = False)
    posts = pagination.items
    return render_template('user.html', user = user, posts = posts, pagination = pagination)

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


@main.route('/write_post', methods=['GET', 'POST'])
@login_required
def write_post():
    '''撰写并提交文章'''
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body = form.body.data, author = current_user._get_current_object())
        db.session.add(post)
        flash('文章提交成功')
        return redirect(url_for('main.index'))
    return render_template('write_post.html', form = form)

@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])

@main.route('/edit/<int:id>', methods = ['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('文章已经更新')
        return redirect(url_for('main.post', id = post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form = form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    '''关注用户视图函数'''
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('没有此用户')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('你已经关注此用户了')
        return redirect(url_for('main.user', username = username))

    current_user.follow(user)
    flash('你关注了 %s.' % username)
    return redirect(url_for('main.user', username=username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    '''取消关注用户视图函数'''
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('没有此用户')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('你没有关注此用户')
        return redirect(url_for('main.user', username = username))
    current_user.unfollow(user)
    flash('你不再关注 %s 了' % username)
    return redirect(url_for('main.user', username = username))

@main.route('/followers/<username>')
def followers(username):
    '''显示你关注的用户'''
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('没有此用户')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type = int)
    pagination = user.followers.paginate(page, per_page = 5,error_out = False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html', user = user, title = "你关注的人",
                           endpoint = 'main.followers', pagination = pagination,
                           follows = follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    '''显示关注你的用户'''
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('没有此用户')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page, per_page = 5,error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}for item in pagination.items]
    return render_template('followers.html', user = user, title = "你被谁关注",
                           endpoint = 'main.followed_by', pagination = pagination,
                           follows = follows)