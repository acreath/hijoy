from flask import render_template, request
from . import main


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
                 not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        eturn response
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
                 not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'Internal server error'})
        response.status_code = 500
        eturn response
    return render_template('500.htnl'), 500


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response

def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def badrequest(message):
    response = jsonify({'error': 'badrequest', 'message': message})
    response.status_code = 400
    return response

def method_not_allowed(message):
    response = jsonify({'error': 'Method not allowed', 'message': message})
    response.status_code = 405
    return response

