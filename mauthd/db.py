from twisted.internet.defer import returnValue, inlineCallbacks
from lib import db as _db

import settings
from secrets import db_password

db = _db.DB(settings, db_password)

"""
    All of these functions run some SQL queries and return a deferred
"""

@inlineCallbacks
def register_and_verify (username, pwhash, email, token, success_url, send_email_cb) :
    """
        Creates the users and users_verify rows for the given registration. Calls send_email_cb,
        and if all of these succeed, commits the transation.

        If any step fails, the transaction is rolled back

        Returns the user_id
    """

    # XXX: user_events

    class state_hack :
        user_id = None
    
    def db_insert (trans) :
        user_id = db._insertForID("""
            INSERT INTO users (
                username, password, email, registered
            ) VALUES (
                %s, %s, %s, now()
            )""", 
                username,
                pwhash,
                email
        )

        state_hack.user_id = user_id

        verify_id = db._insertForID("""
            INSERT INTO users_verify (
                user, token, sent, success_url
            ) VALUES (
                %s, %s, now(), %s
            )""",
                user_id,
                token,
                success_url,
        )

    def run_send_email_cb () :
        return defer.maybeDeferred(send_email_cb(state_hack.user_id))

    yield db.runWithTransaction((
        (db_insert, (), {}),
        (db.wrapUserFunc(run_send_email_cb), (), {}),
    ))

    returnValue( state_hack.user_id )

@inlineCallbacks
def handle_verify (uid, token) :
    """
        Forget about the verify action for the given uid/token

        Returns a (verify_ok, user_ok, user_verified, username, success_url) tuple.
            verify_ok       - the verification succeeded
            user_ok         - the user id exists
            user_verified   - has the user been verified?
            username        - if the veficiation is valid, this is the username
            success_url     - the success url
    """

    verify_select_res = yield db.queryOne("""
        SELECT id, success_url FROM verify_users WHERE
                uid = %s
            AND token = %s
        """,
            uid,
            token
    )
    
    username_res = yield db.queryOne("""
        SELECT username, verified FROM users WHERE
            uid = %s
        """,
            uid,
    )

    if verify_select_res :
        verify_ok = True

        verify_id, success_url = verify_select_res
        
        yield db.modifyForRowcount("""
            DELETE FROM users_verify WHERE
                id = %s
            """,
                verify_id
        )

        yield db.execute("""
            UPDATE users SET verified=now() WHERE
                    uid = %s
            """,
                uid
        )
        
        # XXX: user_events
        
        user_ok = True

        username, user_verified = username_res

    else :
        verify_ok = False
        
        user_ok = bool(username_res)

        if username_res :
            username, user_verified = username_res
        else :
            username = success_url = None

    returnValue( verify_ok, user_ok, user_verified, username, success_url )

@inlineCallbacks
def check_login (username, pw_hash) :
    """
        Returns a user_ok, password_ok, user_id tuple
    """

    res = yield db.queryOne("""
        SELECT id FROM users WHERE
                username    = %s
            AND password    = %s
        """,
            username,
            pw_hash
    )

    if res :
        user_id, = res

        yield db.execute("""
            UPDATE users SET
                last_login = now()
            WHERE
                id = %s
            """,
                user_id
        )
        
        # XXX: user_events

        returnValue( True, True, user_id )
    else :
        res = yield db.queryOne("""
            SELECT id FROM users WHERE
                username    = %s
            """,
                username
        )

        if res :
            user_id, = res

            returnValue( True, False, user_id )
        else :
            returnValue( False, False, None )

