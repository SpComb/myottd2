from twisted.internet.defer import returnValue, inlineCallbacks, maybeDeferred

import settings, errors
from lib import utils
from lib.db import DB, runAsTransaction, callFromTransaction
from secrets import db_password

db = DB(settings, db_password)

"""
    All of these functions run some SQL queries and return a deferred
"""

@runAsTransaction
def register_and_verify (trans, username, pwhash, email, token, success_url_fmt, send_email_cb) :
    """
        Creates the users and users_verify rows for the given registration. Calls send_email_cb,
        and if all of these succeed, commits the transation.

        If any step fails, the transaction is rolled back

        Returns the user_id
    """

    # XXX: user_events
    
    # create the users row
    user_id = db._insertForID(trans, """
        INSERT INTO users (
            username, password, email, registered
        ) VALUES (
            %s, %s, %s, now()
        )""", (
            username,
            pwhash,
            email
    ))
    
    # record the verify token
    verify_id = db._insertForID(trans, """
        INSERT INTO user_verify (
            user_id, token, sent, success_url
        ) VALUES (
            %s, %s, now(), %s
        )""", (
            user_id,
            token,
            success_url_fmt,
    ))
    
    # send the actual email
    cb_ret = callFromTransaction(send_email_cb, user_id)
    
    # return the newly allocated user id
    return user_id

@runAsTransaction
def handle_verify (trans, uid, token) :
    """
        Forget about the verify action for the given uid/token

        Returns a (verify_ok, user_ok, user_verified, username, success_url) tuple.
            verify_ok       - the verification succeeded
            user_ok         - the user id exists
            user_verified   - has the user been verified?
            username        - if the veficiation is valid, this is the username
            success_url     - the success url
    """
    
    # select the verify information based on the given token
    verify_select_res = db._queryOne(trans, """
        SELECT id, success_url FROM user_verify WHERE
                user_id = %s
            AND token = %s
        """,
            uid,
            token
    )
    
    # select the username based on the given uid
    username_res = db._queryOne(trans, """
        SELECT username, verified FROM users WHERE
            id = %s
        """,
            uid,
    )

    if verify_select_res :
        # the verify token was valid
        verify_id, success_url = verify_select_res
        
        # mark the verify token as invalid
        db._modifyForRowcount(trans, """
            DELETE FROM user_verify WHERE
                id = %s
            """,
                verify_id
        )
        
        # mark the user as verified
        db._execute(trans, """
            UPDATE users SET verified=now() WHERE
                    id = %s
            """,
                uid
        )
        
        # XXX: user_events
        
        username, user_verified = username_res

        return username, success_url

    else :
        # did the uid exist?
        if username_res :
            username, user_verified = username_res
            
            # already verified?
            if user_verified :
                raise errors.Verify_AlreadyDone()

            else :
                # must be a bad token
                raise errors.Verify_Token()

        else :
            raise errors.Verify_User()

@inlineCallbacks
def check_login (username, pw_hash) :
    """
        Returns a user_ok, verify_ok, password_ok, user_id tuple
    """
    
    # XXX: this should be a stored procedure
    
    # first look for a valid login
    res = yield db.queryOne("""
        SELECT id FROM v_users_valid WHERE
                username    = %s
            AND password    = %s
        """,
            username,
            pw_hash
    )

    if res :
        # valid login info
        user_id, = res
        
        # update their last_login time
        yield db.execute("""
            UPDATE users SET
                last_login = now()
            WHERE
                id = %s
            """,
                user_id
        )
        
        # XXX: user_events

        # return their uid
        returnValue( user_id )

    else :
        # does the user exist?
        res = yield db.queryOne("""
            SELECT id, verified FROM users WHERE
                username    = %s
            """,
                username
        )
        
        # throw the appropriate error
        if not res :
            raise errors.CheckLogin_Username()

        user_id, verified = res

        if not verified :
            raise errors.CheckLogin_Verified()

        raise errors.CheckLogin_Password()

