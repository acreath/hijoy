from flask import render_template, redirect, request, url_for, flash
from . import auth
from flask_login import login_user, login_required, logout_user, UserMixin
from ..models import User
from .forms import LoginForm, RegistrationForm
from .. import db
from ..email import send_email

#登入用户的逻辑
@auth.route('/auth/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remenber_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html',form=form)


#登出用户逻辑
@auth.route('/auth/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


    
#用户注册逻辑
@auth.route('/auth/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', 
                                user=user, token=token)

        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/secret')
@login_required
def secret():
    return 'Only authenticated users are allowed!'

