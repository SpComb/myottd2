<%inherit file="layout.myt" />

<%def name="tab_header(tabs)">
<%
    global _panel_tabs, _panel_selected_tabs

    _panel_tabs = (tab for tab, desc in tabs)
    _panel_selected_tabs = list(set(_panel_tabs) & set(request.args.iterkeys()))
%>
                    <ul>
% for tab, tab_desc in tabs :
                        <li><a href="?${tab}">${tab_desc}</a></li>
% endfor
                    </ul>
</%def>

<%def name="tab_div_attrs(tab_name, default=False)">
<% _panel_selected_tabs = globals()['_panel_selected_tabs'] %>
id="t_${tab_name}" class="tab"\
% if not (tab_name in _panel_selected_tabs or (not _panel_selected_tabs and default)) :
 style="display: none;"\
% endif
</%def>

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
                        <h1>Account data</h1>
                        
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
                    </div>

                    <div ${tab_div_attrs("email")}>
                        <h1>Email Settings</h1>
                        <p>
                            If you change your email address, you will be required to confirm the new address before you can
                            log in again.
                        </p>

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
                    </div>

                    <div ${tab_div_attrs("servers")}>
                        <h1>Your Servers</h1>
                        <p>
                            You can only have a limited number of servers. Currently this limit is unknown (XXX: ???).
                        </p>

                        <table id="servers" cellspacing="1">
                            <tr>
                                <th>ID #</th>
                                <th>Name</th>
                                <th>Title</th>
                                <th>Clients</th>
                                <th>Companies</th>
                                <th>Version</th>
                                <th>&nbsp;</th>
                            </tr>

                            <tr class="odd">
                                <td>138</td>
                                <td>main</td>
                                <td><a href="http://user1.myottd.net/main">Main</a>
                                </td>
                                <td> 0 / 10 </td>
                                <td> 1 / 8 </td>
                                <td> Stable (0.6.0) </td>
                                <td />
                            </tr>
                            <tr class="even">
                                <td>205</td>
                                <td>test</td>
                                <td><a href="http://user1.myottd.net/test">Test</a></td>
                                <td> 0 / 10 </td>
                                <td> 1 / 8 </td>
                                <td> Nightly (r12684) </td>
                                <td>
                                    <img src="/static/icons/lock.png" />
                                </td>
                            </tr>
                            <tr class="odd">
                                <td>18</td>
                                <td>desert</td>
                                <td><a href="http://user2.myottd.net/desert">Desert Server</a></td>
                                <td> 0 / 10 </td>
                                <td> 0 / 8 </td>
                                <td> Stable (0.6.0) </td>
                                <td />
                            </tr>
                        </table>
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
