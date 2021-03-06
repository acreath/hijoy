from . import db
import pylint_flask
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_required, AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer 
from flask import current_app
from datetime import datetime
import hashlib
from flask import request, url_for
from markdown import markdown
import bleach
from app.exceptions import ValidationError
'''
程序的权限

操  作  |  位  值  |  说  明
关注用户 | 0b00000001(0x01) |关注其他用户
在他人的文章中发表评论 | 0b00000010(0x02) | 在他人撰写的文章中发布评论
写文章 |0b00000100(0x04) | 写原创文章
管理他人发表的评论 | 0b00001000(0x08) | 查处他人发表的不当评论
管理员权限 | 0b10000000(0x80) |管理网站
     
'''

'''
用户角色

用户角色  |  权限  |  说明
匿名 | 0b00000000(0x00) | 未登录的用户。在程序中只有阅读权限
用户 | 0b00000111(0x07) | 具有发布文章、发表评论和关注其他用户的权限。这是新用户的默认角色  
协管员 | 0b00001111(0x0f) | 增加审查不当评论的权限
管理员 | 0b11111111(0xff) | 具有所有权限，包括修改其他用户所属角色的权限
'''
#权限常量
class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean,default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role',lazy='dynamic')


    def __repr__(self):
        return '<Role %r>' % self.name

    #使用这个方法在数据中创建角色
    @staticmethod
    def insert_roles():
        #set the permissions of the different roles
        roles = {
            'User': (Permission.FOLLOW | 
                    Permission.COMMENT | 
                    Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW | 
                          Permission.COMMENT | 
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name = r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

#关注关联表的模型
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    followed_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


#增加用户资料所需要的信息
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), unique=True, index=True)
    confirmed = db.Column(db.Boolean, default=False)
    #用户资料
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(),default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    #博客信息
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    #评论信息
    comments = db.relationship('Comment', backref='author', lazy='dynamic')


    #拆分多对多关系为多对一关系
    followed = db.relationship('Follow',
                                    foreign_keys=[Follow.follower_id],
                                    backref=db.backref('follower', lazy='joined'),
                                    lazy='dynamic',
                                    cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                     foreign_keys=[Follow.followed_id],
                                     backref=db.backref('followed', lazy='joined'),
                                     lazy='dynamic',
                                     cascade='all, delete-orphan')
    
    #赋予用户角色：检测到系统变量中的管理员邮箱时，直接赋予管理员权限
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
            if self.email is not None and self.avatar_hash is None:
                 self.avatar_hash = hashlib.md5(
                     self.email.encode('utf-8')).hexdigest()
        self.follow(self)
    

    #支持基于令牌的认证
    #生成令牌
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                                    expires_in=expiration) 
        return s.dumps({'id': self.id})
    
    #验证令牌
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY']) 
        try:
            data = s.loads(token) 
        except:
            return None
        return User.query.get(data['id'])
    
    
    #设置头像
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
                 url=url, hash=hash, size=size, default=default, rating=rating)



    #刷新用户的最后访问时间,每次收到用户请求时都要调用ping（）方法
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    #权限校验
    def can(self, permissions):
        print("self.role:{} \n".format(self.role))
        print("self.role.permissions:{} \n".format(self.role.permissions))
        print("permission:{} \n".format(permissions))
        print("&:{} \n".format((self.role.permissions & permissions)))
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions
    
    #是否是管理员
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    #计算密码散列值的函数通过名为 password 的只写属性实现
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm':self.id})
    
    def confirm(self, token):
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
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    #随机生成虚拟用户
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py
             
        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(), 
                        username=forgery_py.internet.user_name(True), 
                        password=forgery_py.lorem_ipsum.word(), 
                        confirmed=True, 
                        name=forgery_py.name.full_name(), 
                        location=forgery_py.address.city(), 
                        about_me=forgery_py.lorem_ipsum.sentence(), 
                        member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    #关注关系的辅助方法
    def follow(self, user):#创建关注关系
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
    
    def unfollow(self, user):#取消关注
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
    
    def is_following(self, user):#判断用户B是否被用户A关注
        return self.followed.filter_by(followed_id=user.id).first() is not None
    
    def is_followed_by(self, user):#拿出这个用户B所有的关注者
        return self.followers.filter_by(follower_id=user_id).first() is not None
    
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
             .filter(Follow.follower_id == self.id)
    
    @staticmethod#用户设为自己的关注者
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()
    
    
    #把用户转化为json 格式的序列化字典
    def to_json(self): 
        json_user = {
            'url': url_for('api.get_post', id=self.id, _external=True), 
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts': url_for('api.get_user_posts', id=self.id, _external=True), 
            'followed_posts': url_for('api.get_user_followed_posts',
                                            id=self.id, _external=True), 
            'post_count': self.posts.count()
            }
        return json_user



class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    def is_administrator(self): 
        return False

        
login_manager.anonymous_user = AnonymousUser


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    #随机生成虚拟博客
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        
        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                          timestamp=forgery_py.date.date(True),
                          author=u)
            db.session.add(p)
            db.session.commit()


    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                             'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                             'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
                 markdown(value, output_format='html'),
                 tags=allowed_tags, strip=True))

    #把博客文章转化成序列化的 json 字典，作为响应
    def to_json(self):
        json_post = {
        'url': url_for('api.get_post', id=self.id, _external=True), 'body': self.body,
        'body_html': self.body_html,
        'timestamp': self.timestamp,
        'author': url_for('api.get_user', id=self.author_id,
        _external=True),
        'comments': url_for('api.get_post_comments', id=self.id,
        _external=True),
        'comment_count': self.comments.count()
        }
        return json_post

    #从 json 格式创建一篇博客实例，存入数据库
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        print(body) 
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)


db.event.listen(Post.body, 'set', Post.on_changed_body)



#评论模型
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    #过滤markdown提交时的标签
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                             'strong']
        target.body_html = bleach.linkify(bleach.clean(
                 markdown(value, output_format='html'),
                 tags=allowed_tags, strip=True))
db.event.listen(Comment.body, 'set', Comment.on_changed_body)
