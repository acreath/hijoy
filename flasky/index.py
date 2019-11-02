from flask import Flask,render_template
from flask import request,make_response,redirect,abort
from flask_script import Manager
from flask_bootstrap import Bootstrap

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)


@app.route('/') 
def index():
    """
    user_agent = request.headers.get('User-Agent')
    print("information of request:{}".format(request.headers))
    return '<p>Your browser is %s</p>' %user_agent
    #return '<h1>Hello World!</h1>'
    """
    return render_template('index.html')

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
    user = load_user(id) 
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