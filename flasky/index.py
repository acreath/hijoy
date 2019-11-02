from flask import Flask,render_template,session,redirect,url_for,flash
from flask import request,make_response,redirect,abort
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'hard to guess string'

class NameForm(Form):
    name = StringField('What is your name?',validators=[Required()])
    submit = SubmitField('Submit')


@app.route('/',methods=['GET','POST']) 
def index():
    
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed yor name!')
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'))
    """
    user_agent = request.headers.get('User-Agent')
    print("information of request:{}".format(request.headers))
    return '<p>Your browser is %s</p>' %user_agent
    #return '<h1>Hello World!</h1>'
    
    return render_template('index.html')
    """

@app.route('/user/<name>') 
def user(name):
    return render_template('user.html',name = name)

@app.route('/reponse')
def reponses():
    response = make_response('<h1>This document carries a cookie</h1>')
    response.set_cookie('answer','42')
    
    return response

@app.route('/404')
def red():
    return redirect('http://www.baidu.com')


@app.route('/user/<id>') 
def get_user(id):
    user = load_usr(id) 
    if not user:
        abort(404)
    return '<h1>Hello, %s</h1>' % user.name


@app.errorhandler(404) 
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__': 
    #app.run(debug=True)
    manager.run()