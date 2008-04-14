<%inherit file="layout.myt" />
<%namespace file="_panel.myt" import="*" />

                <h1>Server Control Panel</h1>

                <div id="panel">
                    <div id="tabs">
${tab_header((
    ("control", "Control"),
    ("console", "Console"),
    ("config",  "Config"),
    ("files",    "NewGRFs / Savegames"),
    ("logs",    "Logs"),
    ("stats",   "Statistics"),
))}
                    </div>

                    <div ${tab_div_attrs("control", default=True)}>  
                        <form action="?control" method="POST">
                            <fieldset>
                                <legend>Server Running</legend>

                                <label for="stop">Stop Server</label>
                                <input type="submit" name="submit" id="stop" value="Stop" disabled="disabled" />
                                <br/>
                            </fieldset>

                            <fieldset>
                                <legend>Server Stopped</legend>
                                
                                <label for="cmd_args">Commandline Arguments</label>
                                <input type="text" name="cmd_args" id="cmd_args" />
                                <br/>

                                <label for="start">Start Server</label>
                                <input type="submit" name="submit" id="start" value="Start" />
                                <br/>

                            </fieldset>
                        </form>
                        
                        <h1>Server Control</h1>
                        <p>
                            Here you can control your server's status, i.e. stop it or start it.
                        </p>

                        <h2>Commandline Arguments</h2>
                        <p>
                            This specifies the arguments to pass to OpenTTD on startup (insert link to argument reference here).
                        </p>
                    </div>

                    <div ${tab_div_attrs("console")}>
                        <pre id="console_out">
<span class="stdout">22:54:55  foo bar</span>
<span class="stderr">23:00:23  quux asdf</span>
<span class="status">--- Day Changed to 2008/04/14</span>
<span class="stdin" >01:39:18  foobar</span>
<span class="status">01:39:18  raks poks</span>
                        </pre>

                        <form action="?console" method="POST" id="console_input">
                            <p>
                                <input type="text" name="input" id="input" />
                                <input type="submit" name="submit" id="submit" value="Send" />
                            </p>
                        </form>

                        <h1>The Console</h1>
                        <p>
                            The console lets you view your server's status/debugging output, as well as feed it commands and read
                            the results. Additionally, some of MyOTTD's own status messages show up in the output.
                        </p>

                        <p>
                            The contents of the console are colour-coded based on the source of the lines, as follows:
                            
                            (how do you do those def-list things? stdout=blue, stderr=red, stdin=green, status=black)
                        </p>
                        <p>
                            (insert shitloads of info about the various commands here)
                        </p>
                    </div>

                    <div ${tab_div_attrs("config")}>
                        <form action="?config" method="POST">
                            <textarea cols="120" rows="80">
[patches]
foobar=1
asdjfoijas=3
asiodjfoi=3

[network]
server_bind_ip=
server_pw=12345
server_name=foo.myottd.net/bar - quux
                            </textarea>
                            
                            <p>
                                <input type="submit" name="submit" value="Update Config" />
                                <br/>

                                <a href="/account/servers/${server_name}/config">Direct link to raw config</a>
                            </p>
                        </form>

                        <h1>The Configuration</h1>
                        <p>
                            The configuration is the contents of the openttd.cfg file that OpenTTD uses to configure most of its behaviour,
                            and you can edit it here.
                        </p>
                        <p>
                            (insert shitloads of info about the various configuration directives here)
                        </p>
                    </div>

                    <div ${tab_div_attrs("files")}>
                        <div id="files">
                            <div id="breadcrumb">
                                <a href="?files=/">root</a> / <a href="?files=/ottd/">ottd</a> / <a href="?files=/ottd/data/">data</a> /
                            </div>
                            <ul>
% for fname in ("..", "shared/", "openttdw.grf", "openttdd.grf", "opntitle.dat", "sample.cat", "trg1r.grf", "trfcr.grf", "trghr.grf", "trgir.grf", "trgtr.grf") :
                                <li><a href="?files=/ottd/data/${fname}">${fname}</a></li>
% endfor                                
                            </ul>

                            <form action="/account/servers/desert/upload" method="POST" enctype="multipart/form-data" id="files_upload">
                                <label for="file">Upload File/Archive</label>
                                <input type="file" name="file" id="file" />
                                <input type="submit" name="submit" id="submit" value="Upload" />
                            </form>
                        </div>

                        <h1>NewGRFS / Savegames</h1>
                        <p>
                            This view is a general-purpose file browser for this server's filesystem.
                        </p>

                        <h2>Browsing Directories</h2>
                        <p>
                            Browsing directories (folders) works by clicking on the names of folders in the breadcrumb or file list.
                        </p>

                        <h2>Viewing Files</h2>
                        <p>
                            Clicking on a file will show you that file's information, with options to delete, rename or download the file.
                        </p>

                        <h2>Uploading Files / Archives</h2>
                        <p>
                            It is also possible to upload new files from your local hard drive to the server.

                            Simply choose a file and hit Upload to upload it into the currently visible directory (this may fail due to permission
                            issues, beware of those).
                        </p>
                        <p>
                            It is also possible to upload entire archives, which will be extracted into the current folder. Accepted formats are .zip, .tar.gz and .tar.bz2.
                        </p>
                    </div>
                    
                    <div ${tab_div_attrs("logs")}>
                        <h1>Todo</h1>
                    </div>

                    <div ${tab_div_attrs("stats")}>
                        <h1>Todo</h1>
                    </div>
                </div>
