from twisted.internet.defer import returnValue, inlineCallbacks

from lib import utils, api
import db, verify, email, settings, errors

@inlineCallbacks
def xmlrpc_register_user (ctx, username, pw_hash, email_addr, success_url) :
    """
        New user wants to register. We need to create the row in the database, and send the verification email.
        
        Once the verification suceeds, the user will be redirected to the given success_url, which may contain
        python named string formatting codes for the following tokens:
            user_id     - the numeric user ID
            username    - the username        

        Returns the user_id
    """
    
    token = verify.generateToken(username, pw_hash, email_addr)
    
    @inlineCallbacks
    def send_email_cb (user_id) :
        verify_url = utils.build_url(settings.verify_url,
            user_id = user_id,
            token   = token,
        )

        email_body = email.build_verify_email(
            from_addr       = settings.from_email,
            site_name       = settings.site_name,
            site_url        = settings.site_url,
            admin_contact   = settings.admin_contact,
            username        = username,
            verify_token    = token,
            verify_url      = verify_url,
            email           = email_addr,
        )
        
        yield email.send_email(settings.smtp_server, settings.from_email, email_addr, email_body)
    
    user_id = yield db.register_and_verify(username, pw_hash, email_addr, token, success_url, send_email_cb)

    returnValue( user_id )

@inlineCallbacks
def xmlrpc_check_login (ctx, username, pw_hash) :
    """
        Verify the given login information.

        Returns the user_id
    """

    username_ok, verify_ok, password_ok, user_id = yield db.check_login(username, pw_hash)

    if not username_ok :
        raise errors.CheckLogin_Username()

    elif not verify_ok :
        raise errors.CheckLogin_Verify()

    elif not password_ok :
        raise errors.CheckLogin_Password()

    else :
        returnValue( user_id )

@inlineCallbacks
def http_verify (ctx, uid, token) :
    """
        Attempt to verify the given user with the given token. If it succeeds, the verification url should be invalidated,
        and the account marked as verified.
        
        Shows a message to the user, and possibly redirects them to the success_url defined for the verify action
    """

    username, success_url = yield db.handle_verify(user_id, token)
    
    success_url = utils.build_url(success_url,
        uid         = user_id,
        username    = username,
    )

    ctx.redirectTo(success_url)

    returnValue( ("Account '%s' successfully activated" % username) )

