from datetime import datetime
from flask import request,render_template, session, redirect, \
    url_for, flash, current_app

from . import main
from .forms import NameForm, EditProfileForm,EditProfileAdminForm,PostForm
from .. import db
from ..models import User, Post
from flask_login import login_required, current_user

from ..decorators import admin_required, permission_required
from ..models import Permission 

##如何使用修饰器对权限进行检测

@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return "For administrators!"


@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderators_only():
    return "For comment moderators!"

#处理博客文章的首页路由
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
        form.validate_on_submit():
        post = Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    #posts = Post.query.order_by(Post.timestamp.desc()).all()

    #分页显示博客文章列表
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
             error_out=False)
    posts = pagination.items
    return render_template('index.html', 
                            form = form, posts=posts, pagination=pagination)
    

#用户资料路由
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user',username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


#管理员的资料编辑路由
@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)#能不能拿到这个id，不能就报404
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

#文章固定链接
@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)#这个是根据id查找数据时专用的函数
    return render_template('post.html',posts=[post])
  
#编辑博客文章
@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    #如果这个用户既不是博客的作者也不是管理员
    if current_user.id != post.author_id and\
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been update.')
        return redirect(url_for('.post', id=post.id))#回顾一下redirect函数
    form.body.data = post.body#用户刷新页面时，不会出发post请求，使用get请求加载原有的内容
    return render_template('edit_post.html',form=form)
