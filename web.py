from twisted.web2 import server, http, resource, channel, static
import mako, mako.template, mako.lookup

templates = mako.lookup.TemplateLookup(directories=['templates'], module_directory='cache/templates-web', output_encoding='utf-8')

def render_template (tpl, **data) :
    return templates.get_template(tpl).render(**data)

class Root (resource.Resource) :
    addSlash = True
    
    def render (self, ctx) :
        return http.Response(stream=render_template("index.myt"))

def template_resource (tpl) :
    class Res (resource.Resource) :
        addSlash = False
        
        def render (self, req) :
            return http.Response(
                stream=render_template(tpl,
                    request         = req,
                
                )
            )
    
    return Res()

root = Root()

for url, resource in (
    ("static",      static.File("static/")),
    ("register",    template_resource("register.myt")),
    ("login",       template_resource("login.myt")),
    ("pwreset",     template_resource("pwreset.myt")),
    ("versions",    template_resource("versions.myt")),
    ("servers",     template_resource("servers.myt")),
    ("account",     template_resource("account.myt")),
) :
    root.putChild(url, resource)

site = server.Site(root)

from twisted.application import service, strports
application = service.Application("myottd")
s = strports.service('tcp:8080', channel.HTTPFactory(site))
s.setServiceParent(application)

