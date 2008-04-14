from twisted.internet import reactor
from twisted.web import server, http, resource, static
import twisted.web.resource
import mako, mako.template, mako.lookup

import monkeypatch_twisted_web_novalue_args

templates = mako.lookup.TemplateLookup(directories=['templates'], module_directory='cache/templates-web', output_encoding='utf-8')

def render_template (tpl, **data) :
    return templates.get_template(tpl).render(**data)

class View (object, twisted.web.resource.Resource) :
    def __init__ (self) :
        twisted.web.resource.Resource.__init__(self)

class SimpleTemplateView (View) :
    def __init__ (self, tpl, **kwargs) :
        self.tpl = tpl
        self.context = kwargs

        super(SimpleTemplateView, self).__init__()

    def render_GET (self, req) :
        ctx = dict(
            request         = req,
        )

        ctx.update(self.context)
        
        return render_template(self.tpl, **ctx)

class AccountManageServerView (SimpleTemplateView) :
    def __init__ (self, server_name) :
        self.server_name = server_name

        super(AccountManageServerView, self).__init__("account_server.myt", server_name=server_name)

class AccountServersView (View) :
    def render_GET (self, request) :
       request.redirect("/account?servers") 

       return ""

    def getChild (self, name, request) :
        return AccountManageServerView(name)

class AccountView (SimpleTemplateView) :
    def __init__ (self) :
        super(AccountView, self).__init__("account.myt")

class RootView (SimpleTemplateView) :
    def __init__ (self) :
        super(RootView, self).__init__("index.myt")

account_view = AccountView()
account_view.putChild('servers', AccountServersView())

root = resource.Resource()
root.putChild('', RootView())
root.putChild('account', account_view)

for url, resource in (
    ("static",      static.File("static/")),
    ("register",    SimpleTemplateView("register.myt")),
    ("login",       SimpleTemplateView("login.myt")),
    ("pwreset",     SimpleTemplateView("pwreset.myt")),
    ("versions",    SimpleTemplateView("versions.myt")),
    ("servers",     SimpleTemplateView("servers.myt")),

) :
    root.putChild(url, resource)

site = server.Site(root)

reactor.listenTCP(8080, site)
reactor.run()

