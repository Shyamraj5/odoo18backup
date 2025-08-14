from functools import wraps
from odoo.http import request
from datetime import datetime
import json

def is_token_valid(token):
    try:
        token = token.split(' ')[1]
        return request.env['mobile.api.token'].sudo().validate_token(token)
    except:
        return False

def validate_token(func):
    """
    Decorator to validate token before executing the route handler.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Retrieve token from the request headers
        token = request.httprequest.headers.get('Authorization')
        if not token:
            return request.make_response(
                json.dumps({
                    "statusOk": False,
                    "statusCode": 401,
                    "message": "Unauthorized",
                    "payload": None,
                    "error": "Unauthorized"
                }),
                [('Content-Type', 'application/json')],
                status=401
            )
        
        # Validate the token
        validated_data = is_token_valid(token)
        if not validated_data:
            return request.make_response(
                json.dumps({
                    "statusOk": False,
                    "statusCode": 401,
                    "message": "Token is invalid or expired",
                    "payload": None,
                    "error": "Unauthorized"
                }),
                [('Content-Type', 'application/json')],
                status=401
            )
        request.validated_token = validated_data
        
        return func(*args, **kwargs)
    return wrapper