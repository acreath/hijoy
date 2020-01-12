from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User,AnonymousUser
from . import api
from .errors import unauthorized, forbidden

#先创建一个对象，由于这种用户认证方法只在API蓝本中使用，
# 所以只需要在蓝本包中初始化
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        g.current_user = AnonymousUser() 
        return True
        
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token.lower()).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


#本来是自动生产401，为了和 API 返回的其他错误保持一致，我们可以自定义这个错误响应
@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


#如果现在的用户是匿名用户与和没有认证
@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


#生成认证令牌
@api.route('/tokens/', methods=['POST'])
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})

