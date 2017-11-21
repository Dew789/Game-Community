#!/usr/bin/env python
from functools import wraps
from flask import abort
from flask.ext.login import current_user
from .models import Permission

def permission_required(permission):
    '''自定义装饰器，在用户没有权限进入页面时显示时，返回403'''
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    '''定义管理员权限修饰器'''
    return permission_required(Permission.ADMINISTER)(f)