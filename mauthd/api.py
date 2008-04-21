from twisted.internet.defer import returnValue, inlineCallbacks

import db, verify, email, settings

@inlineCallbacks
def api_register_user (ctx, username, pw_hash, email, success_url) :
    """
        New user wants to register. We need to create the row in the database, and send the verification email.
        
        Once the verification suceeds, the user will be redirected to the given success_url, which may contain
        python named string formatting codes for the following tokens:
            uid         - the numeric user ID
            username    - the username        

        Returns the user_id
    """
    
    token = verify.generateToken(uid, username, pwhash, email)
    
    @inlineCallbacks
    def send_email_cb (user_id) :
        verify_url = utils.build_url(settings.verify_url,
            uid     = user_id,
            token   = token,
        )

        email_body = email.build_verify_email(
            site_name       = settings.site_name,
            site_url        = settings.site_url,
            admin_contact   = settings.admin_contact,
            username        = username,
            verify_token    = token,
            verify_url      = verify_url,
            email           = email,
        )
        
        yield email.send_email(settings.smtp_server, settings.from_email, email, email_body)

    user_id = yield db.register_and_verify(username, pw_hash, email, token, success_url, send_email_cb)

    returnValue( user_id )

class LoginError (Exception) :
    def __str__ (self) :
        return "Login error"

class LoginUsernameError (LoginError) :
    def __str__ (self) :
        return "Login error (Unknown username)"

class LoginPasswordError (LoginError) :
    def __str__ (self) :
        return "Login error (Bad password)"

@inlineCallbacks
def api_check_login (ctx, username, pw_hash) :
    """
        Verify the given login information.

        Returns the user_id
    """

    username_ok, password_ok, user_id = yield db.check_login(username, pw_hash)

    if not username_ok :
        raise LoginUsernameError()

    elif not password_ok :
        raise LoginPasswordError()

    else :
        return user_id

