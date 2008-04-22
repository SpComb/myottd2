import urllib

def build_url (fmt, **values) :
    """
        Build the verify-action URL for the email, as specified by the format in settings.verify_url
    """

    return fmt % dict((key, urllib.quote(str(value), '')) for key, value in values.iteritems())


