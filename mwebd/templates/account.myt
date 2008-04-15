<%inherit file="layout.myt" />
<%namespace file="_panel.myt" import="*" />

                <h1>User Control Panel</h1>

                <div id="panel">
                    <div id="tabs">
${tab_header((
    ("account", "Account"),
    ("email", "Email"),
    ("servers", "Servers"),
    ("new_server", "Create Server"),
    ("foobar", "Foobar"),
))}
                    </div>

                    <div ${tab_div_attrs("account", default=True)}>  
                        <form action="?account" method="POST">
                            <fieldset>
                                <legend>Password</legend>

                                <label for="cur_pw">Current Password</label>
                                <input type="password" name="cur_pw" id="cur_pw" />
                                <br/>

                                <label for="new_pw">New Password</label>
                                <input type="password" name="new_pw" id="new_pw" />
                                <br/>
                                
                                <label for="new_pw2">New Password (repeat)</label>
                                <input type="password" name="new_pw2" id="new_pw2" />
                                <br/>

                            </fieldset>

                            <p>
                                <input type="submit" name="submit" value="Change Password" />
                            </p>
                        </form>
                        
                        <h1>Account data</h1>

                        <h2>Change Password</h2>
                        <p>
                            To change your password, you need to enter in your current password as well.
                        </p>
                    </div>

                    <div ${tab_div_attrs("email")}>
                        <form action="?email" method="POST">
                            <fieldset>
                                <legend>Change Email Address</legend>

                                <label for="new_email">New Email Address</label>
                                <input type="text" name="new_email" id="new_email" />
                                <br/>

                                <label for="new_email2">New Email Address (repeat)</label>
                                <input type="text" name="new_email2" id="new_email2" />
                                <br/>

                                <label for="cur_pw">Current Password</label>
                                <input type="password" name="cur_pw" id="cur_pw" />
                                <br/>
                            </fieldset>

                            <p>
                                <input type="submit" name="submit" value="Change Email Address" />
                            </p>
                        </form>
                        
                        <h1>Email Settings</h1>
                        <p>
                            If you change your email address, you will be required to confirm the new address before you can
                            log in again.
                        </p>
                        <p>
                            You must also verify your current password to be able to change your email address.
                        </p>
                    </div>

                    <div ${tab_div_attrs("servers")}>
                        <table id="servers" cellspacing="1">
                            <tr>
                                <th>&nbsp;</th>
                                <th>ID #</th>
                                <th>Name</th>
                                <th>Title</th>
                                <th>Clients</th>
                                <th>Companies</th>
                                <th>Version</th>
                                <th>&nbsp;</th>
                            </tr>

                            <tr class="odd">
                                <td><img src="/static/icons/server-status-on.png" alt="server-status-on" title="Active" /></td>
                                <td>138</td>
                                <td><a href="/account/servers/main">main</a>
                                <td>Main</td>
                                <td> 0 / 10 </td>
                                <td> 1 / 8 </td>
                                <td> Stable (0.6.0) </td>
                                <td />
                            </tr>
                            <tr class="even">
                                <td><img src="/static/icons/server-status-off.png" alt="server-status-off" title="Inactive" /></td>
                                <td>205</td>
                                <td><a href="/account/servers/test">test</a></td>
                                <td>Test</td>
                                <td> 0 / 10 </td>
                                <td> 1 / 8 </td>
                                <td> Nightly (r12684) </td>
                                <td>
                                    <img src="/static/icons/lock.png" />
                                </td>
                            </tr>
                            <tr class="odd">
                                <td><img src="/static/icons/server-status-error.png" alt="server-status-error" title="Error!" /></td>
                                <td>18</td>
                                <td><a href="/account/servers/desert">desert</a></td>
                                <td>Desert Server</td>
                                <td> 0 / 10 </td>
                                <td> 0 / 8 </td>
                                <td> Stable (0.6.0) </td>
                                <td />
                            </tr>
                        </table>
                        
                        <h1>Your Servers</h1>
                        <p>
                            You can only have a limited number of servers. Currently this limit is unknown (XXX: ???).
                        </p>

                        <h2>Status</h2>
                        <p>
                            The status is shown in terms of weather icons (because I couldn't find any better ones...). Sunny is good, Moon
                            is server-offline, thunderstorm is warning, severe-weather-alert is error.
                        </p>

                        <h2>Manage / Configure</h2>
                        <p>
                            Click on the server name to access the server's control panel.
                        </p>
                    </div>

                    <div ${tab_div_attrs("new_server")}>
                        <form action="?new_server" method="POST">
                            <fieldset>
                                <legend>Create Server</legend>

                                <label for="name">Name</label>
                                <input type="text" name="name" id="name" />
                                <br/>

                                <label for="title">Title</label>
                                <input type="text" name="title" id="title" />
                                <br/>

                                <label for="version">OpenTTD Version</label>
                                <select name="version">
                                    <option value="rel_060">Stable (0.6.0)</option>
                                    <option value="r12696">Current Nightly (r12696)</option>
                                    <option value="rel_053">Old Stable (0.5.3)</option>
                                    <option value="other">Other (a longer list)</option>
                                </select>
                                <br/>

                                <label for="password">Password?</label>
                                <input type="text" name="password" id="password" />
                                <br/>
                            </fieldset>

                            <p>
                                <input type="submit" name="submit" value="Create Server" />
                            </p>
                        </form>

                        <h1>Create a New Server</h1>
                        <p>
                            Use this form to create a new server.
                        </p>

                        <h2>Name / Title</h2>
                        <p>
                            These are used to build your server's default name (what shows up in the <a href="http://servers.openttd.org/">OpenTTD server list</a>).
                            It will be of the form <strong>username.myottd.net/name - title</strong>.
                        </p>

                        <h2>Version</h2>
                        <p>
                            The version of OpenTTD to run. See the <a href="/versions">list of OpenTTD versions</a> for more information.
                            If you're not sure what version to select, you should probably use the same one that you use yourself
                            (insert instructions on how to figure that out).
                        </p>

                        <h2>Password</h2>
                        <p>
                            Enter a password here if you want your server to be password-protected, or leave it blank to have it remain public.
                            Note that the password shouldn't contain spaces at the start or the end.
                        </p>
                    </div>

                    <div ${tab_div_attrs("foobar")}>
                        <h1>Foobar panel</h1>
                    </div>
                </div>
