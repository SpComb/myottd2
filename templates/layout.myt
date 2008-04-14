<html>
    <head>
        <title>MyOTTD</title>
% for style in ("style", "fieldset", "servers", "panel", "console", "files") :
        <link rel="Stylesheet" type="text/css" href="/static/${style}.css" />
% endfor        
    </head>
    <body>
        <div id='outer'>
            <div id='header'>
                MyOTTD
            </div>
            <div id='nav'>
                <div id='nav_right'>
                    <ul>
                        <li><a href="/login">Login</a></li>
                        <li><a href="/register">Register</a></li>

                    </ul>
                </div>
                <ul>
                    <li>
                        <a href="/">MyOTTD</a> 
                        <a href="/servers">Servers</a>
                        <a href="/versions">OpenTTD Versions</a>
                    </li>
                </ul>
            </div>

            <div id='content'>
            ${next.body()}
            </div>
            <div id='footer'>

            </div>
        </div>
    </body>
</html>


