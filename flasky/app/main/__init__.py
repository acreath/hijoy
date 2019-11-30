from flask import Blueprint
from ..models import Permission

main = Blueprint('main', __name__)

#使用上下文处理器，让Permission类在模板中能够全局可访问

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

    
from . import views, errors