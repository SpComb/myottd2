
class AuthError (Exception) :
    def __init__ (self, what) :
        self.what = what

    def __str__ (self) :
        return "Authentication error (%s)" % self.what

def auth (secrets) :
    def decorator (func) :
        def _auth_wrapper (self, auth_method, auth_data, params) :
            if auth_method == 'plain' :
                if len(auth_data) != 2 :
                    raise AuthError("auth_data")

                username, secret = auth_data

                if username not in secrets :
                    raise AuthError("user")

                if secrets[username] != secret :
                    raise AuthError("secret")
                
                return func(self, *params)
            else :
                raise AuthError("auth_method")
        return _auth_wrapper
    return decorator
