<%inherit file="layout.myt" />

                <form action="/register" method="POST">
                    <fieldset>
                        <legend>Login Details</legend>
                        
                        <label for="username">Username</label>
                        <input type="text" name="username" id="username" />
                        <br/>

                        <label for="password">Password</label>
                        <input type="password" name="password" id="password" />
                        <br/>
                    </fieldset>

                    <p>
                        <input type="submit" name="submit" value="Login" />
                    </p>
                </form>

                <p>
                    <a href="/pwreset">Forgotten username/password?</a>
                </p>


