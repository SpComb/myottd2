<%inherit file="layout.myt" />
                
                <p>
                    If you already have an account, use the <a href="/login">Login</a> page instead.
                </p>

                <form action="/register" method="POST">
                    <fieldset>
                        <legend>Login Details</legend>
                        
                        <label for="username">Username</label>
                        <input type="text" name="username" id="username" />
                        <br/>

                        <label for="password">Password</label>
                        <input type="password" name="password" id="password" />
                        <br/>

                        <label for="password2">Password (repeat)</label>
                        <input type="password" name="password2" id="password2" />
                        <br/>
                    </fieldset>

                    <fieldset>
                        <legend>Email</legend>

                        <label for="email">Email address</label>
                        <input type="text" name="email" id="email" />
                        <br/>
                        
                        <label for="email2">Email address (repeat)</label>
                        <input type="text" name="email2" id="email2" />
                        <br/>
                    </fieldset>
                    
                    <p>
                        <input type="submit" name="submit" value="Register" />
                    </p>
                </form>

                <h1>Your Username</h1>
                <p>
                    Your username will be used to identify your servers to other people. Specifically, it will be used as part of
                    the <strong>username.myottd.net/servername</strong> URL, which places certain requirements on it.
                </p>

                <p>
                    It can only consist of lowercase letters (a-z), numbers (0-9, but not as the first letter) and hyphens (-, but
                    not as the first or last letters. Two consecutive hypens are also invalid). Uppercase letters are valid, but
                    will be forced into lowercase letters.
                </p>

                <h1>Your Email Address</h1>
                <p>
                    You will be required to confirm your email address before you can log in.
                </p>

                <p>
                    Your email address will only be used for messages requested by you, such as password reset requests.
                    Your address will be kept hidden from other users and will not be revealed or used by other entities than
                    MyOTTD.
                </p>


