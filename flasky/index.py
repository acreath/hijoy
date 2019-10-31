from flask import Flask
from flask import request,make_response,redirect,abort




app = Flask(__name__)

@app.route('/') 
def index():
    
    user_agent = request.headers.get('User-Agent')
    print("information of request:{}".format(request.headers))
    return '<p>Your browser is %s</p>' %user_agent
    #return '<h1>Hello World!</h1>'


@app.route('/user/<name>') 
def user(name):
    return '<h1>Hello, %s!</h1>' % name

@app.route('/reponse')
def reponses():
    response = make_response('<h1>This document carries a cookie</h1>')
    response.set_cookie('answer','42')
    
    return response

@app.route('/404')
def red():
    return redirect('http://www.example.com')


@app.route('/user/<id>') 
def get_user(id):
    user = load_user(id) 
    if not user:
        abort(404)
    return '<h1>Hello, %s</h1>' % user.name

if __name__ == '__main__': 
    app.run(debug=True)