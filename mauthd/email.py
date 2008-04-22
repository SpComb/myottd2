from twisted.internet import reactor, defer
from twisted.mail.smtp import ESMTPSenderFactory
import cStringIO

def send_email (smtp_server, from_addr, to_addr, body) :
    d = defer.Deferred()

    sender = ESMTPSenderFactory(
        None, None,
        from_addr, to_addr,
        cStringIO.StringIO(body),
        d,
        requireAuthentication=False,
        requireTransportSecurity=False
    )

    reactor.connectTCP(smtp_server, 'smtp', sender)

    return d

def _build_email (template, required_tokens, **values) :
    req_set = set(required_tokens)
    val_set = set(values.iterkeys())

    if req_set != val_set :
        raise ValueError("Missing/Extra tokens for email template: %s/%s" % (" ".join(req_set - val_set), " ".join(val_set - req_set)))

    return template % values

def build_verify_email (**kwargs) :
    return _build_email("""\
From: %(from_addr)s\r
To: %(email)s\r
Subject: %(site_name)s Account Registration / Verification\r
\r
Hi!

A new account was registered at %(site_url)s using this email address.

    username :      %(username)s
       email :      %(email)s
verify token :      %(verify_token)s

To activate your new account, you must visit the URL below. If this doesn't work, please contact the admin as listed in the signature below.

    %(verify_url)s

If you did not register this account, simply ignore this email, do not visit the URL above, and the account registration will expire within four days.

Thank you for registering!

---
%(site_name)s
%(site_url)s
%(admin_contact)s

    """, "from_addr site_name site_url admin_contact username verify_token email verify_url".split(), **kwargs)
    
