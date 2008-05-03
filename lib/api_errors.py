from api import fault

Request_Format      = fault( 1011,  "api.format",           "Invalid format of request data (auth/req tuple)"   )
Auth_Format         = fault( 1021,  "api.auth.format",      "Invalid format of authentication data" )
Auth_Method         = fault( 1022,  "api.auth.method",      "Invalid API authentication method"     )
Auth_Username       = fault( 1091,  "api.auth.username",    "Invalid username"                      )
Auth_Password       = fault( 1092,  "api.auth.password",    "Invalid password"                      )

Internal            = fault( 1000,  "api.internal",         "Internal error"                        )

