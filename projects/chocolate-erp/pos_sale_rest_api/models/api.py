from odoo import models, fields, api
from odoo.exceptions import ValidationError

import jwt
import uuid
import datetime
import base64
import os

class MobileAPIToken(models.Model):
    _name = 'mobile.api.token'
    _description = 'Mobile API Bearer Token Management'

    user_id = fields.Many2one('res.users', string='User', required=True)
    token = fields.Char('Access Token', required=True, index=True)
    refresh_token = fields.Char('Refresh Token', required=True)
    expiry = fields.Datetime('Token Expiry')
    refresh_expiry = fields.Datetime('Refresh Token Expiry')
    device_identifier = fields.Char('Device Identifier')


    @api.model
    def delete_expired_refresh_tokens(self):
        """ Deletes all tokens where the refresh token has expired """
        expired_tokens = self.search([('refresh_expiry', '<', fields.Datetime.now())])
        expired_tokens.unlink() 
        return True

    @api.model
    def _get_secret_key(self):
        """
        Generate or retrieve a secure secret key for JWT signing
        """
        # Check if secret key exists in system parameters
        secret_key = self.env['ir.config_parameter'].sudo().get_param('mobile_api.jwt_secret_key')
        
        if not secret_key:
            # Generate a new secret key if not exists
            secret_key = base64.b64encode(os.urandom(64)).decode('utf-8')
            self.env['ir.config_parameter'].sudo().set_param('mobile_api.jwt_secret_key', secret_key)
        
        return secret_key

    @api.model
    def create_token(self, user, device_identifier=None):
        """
        Create JWT Bearer tokens with enhanced security
        
        Args:
            user (res.users): Odoo user record
            device_identifier (str, optional): Unique device identifier
        
        Returns:
            dict: Access and refresh tokens with their details
        """
        
        # Secret key for JWT signing
        secret_key = self._get_secret_key()

        # Token expiration times
        access_token_expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
        refresh_token_expiry = datetime.datetime.now() + datetime.timedelta(days=7)

        # Payload for access token
        access_token_payload = {
            'sub': user.id,  # Subject (user ID)
            'name': user.name,
            'email': user.email,
            'exp': int(access_token_expiry.timestamp()),
            'iat': int(datetime.datetime.now().timestamp()),
            'jti': str(uuid.uuid4()),  # Unique token identifier
            'device': device_identifier
        }

        # Payload for refresh token
        refresh_token_payload = {
            'sub': user.id,
            'exp': int(refresh_token_expiry.timestamp()),
            'type': 'refresh',
            'jti': str(uuid.uuid4())
        }

        # Generate JWT tokens
        access_token = jwt.encode(access_token_payload, secret_key, algorithm='HS256')
        refresh_token = jwt.encode(refresh_token_payload, secret_key, algorithm='HS256')

        # Create token record
        token_record = self.create({
            'user_id': user.id,
            'token': access_token,
            'refresh_token': refresh_token,
            'expiry': access_token_expiry,
            'refresh_expiry': refresh_token_expiry,
            'device_identifier': device_identifier
        })

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'access_token_expiry': int(access_token_expiry.timestamp()),
            'refresh_token_expiry': int(refresh_token_expiry.timestamp())
        }

    @api.model
    def validate_token(self, token):
        """
        Validate JWT Bearer token
        
        Args:
            token (str): JWT token to validate
        
        Returns:
            res.users: User record if token is valid, else False
        """
        try:
            secret_key = self._get_secret_key()
            
            # Decode and validate token
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # Find corresponding user
            user = self.env['res.users'].browse(payload['sub'])
            
            # Additional token validation
            token_record = self.search([
                ('user_id', '=', user.id),
                ('token', '=', token),
                ('expiry', '>', datetime.datetime.now())
            ], limit=1)
            
            return user if token_record else False
        
        except jwt.ExpiredSignatureError:
            # Token has expired
            return False
        except jwt.InvalidTokenError:
            # Invalid token
            return False

    @api.model
    def _refresh_token(self, refresh_token):
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token (str): Existing refresh token
        
        Returns:
            dict: New access and refresh tokens
        """
        try:
            secret_key = self._get_secret_key()
            
            # Decode and validate refresh token
            payload = jwt.decode(refresh_token, secret_key, algorithms=['HS256'])
            
            # Ensure it's a refresh token
            if payload.get('type') != 'refresh':
                raise ValidationError("Invalid refresh token")
            
            # Find user
            user = self.env['res.users'].browse(payload['sub'])
            
            # Check if refresh token exists and is valid
            token_record = self.search([
                ('user_id', '=', user.id),
                ('refresh_token', '=', refresh_token),
                ('refresh_expiry', '>', datetime.datetime.now())
            ], limit=1)
            
            if not token_record:
                raise ValidationError("Invalid or expired refresh token")
            
            # Delete old token record
            token_record.unlink()
            
            # Create and return new tokens
            return self.create_token(user)
        
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise ValidationError("Invalid refresh token")

    @api.model
    def revoke_tokens(self, user=None, device_identifier=None, token=None):
        """
        Revoke tokens for a user or specific device
        
        Args:
            user (res.users, optional): User to revoke tokens for
            device_identifier (str, optional): Specific device to revoke
        """
        domain = []
        
        if user:
            domain.append(('user_id', '=', user.id))
        
        if device_identifier:
            domain.append(('device_identifier', '=', device_identifier))

        if token:
            domain.append(('token', '=', token))
        
        if domain:
            tokens = self.search(domain)
            tokens.unlink()


class SyncTracking(models.Model):
    _name = 'sync.tracking'
    _description = 'Sync Tracking'

    model_name = fields.Char(string='Model Name', required=True)
    last_sync_date = fields.Datetime(string='Last Sync Date')

# Requirements for this implementation
# Add to requirements.txt or setup.py
# PyJWT==2.7.0