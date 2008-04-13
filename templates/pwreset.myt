<%inherit file="layout.myt" />
                
                <h1>Forgotten Username/Password?</h1>
                <p>
                    If you forgot your username/password, no need to worry, just enter the email address that you registered with
                    in the form below to have a password reset link sent to you.
                </p>

                <form action="/pwreset" method="POST">
                    <fieldset>
                        <legend>Password Reset</legend>

                        <label for="email">Email address</label>
                        <input type="text" name="email" id="email" />
                        <br/>

                    </fieldset>
                    
                    <p>
                        <input type="submit" name="submit" value="Reset Password" />
                    </p>
                </form>

