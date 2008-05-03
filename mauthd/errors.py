"""
    auth API errors
"""

from lib.api import fault

CheckLogin_Verified         = fault(2011,   "auth.check_login.not_verified",    "Login error (Not verified)"        )
CheckLogin_Username         = fault(2012,   "auth.check_login.bad_username",    "Login error (Unknown username)"    )
CheckLogin_Password         = fault(2013,   "auth.check_login.bad_password",    "Login error (Bad password)"        )

Verify_User                 = fault(2021,   "auth.verify.uid",                  "No such user"                      )
Verify_Token                = fault(2022,   "auth.verify.token",                "Invalid verification token"        )
Verify_AlreadyDone          = fault(2023,   "auth.verify.alreadydone",          "User has already been verified"    )

