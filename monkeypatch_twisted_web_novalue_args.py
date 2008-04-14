import twisted.web.http

_parse_qs = twisted.web.http.parse_qs

def parse_qs (qs, keep_blank_values=0, strict_parsing=0, unquote=twisted.web.http.unquote) :
    """like cgi.parse_qs, only with custom unquote function"""
    d = {}
    items = [s2 for s1 in qs.split("&") for s2 in s1.split(";")]
    for item in items:
        try:
            k, v = item.split("=", 1)
        except ValueError:
            k = item
            v = ""

        if v or keep_blank_values:
            k = unquote(k.replace("+", " "))
            v = unquote(v.replace("+", " "))
            if k in d:
                d[k].append(v)
            else:
                d[k] = [v]
    return d

twisted.web.http.parse_qs = parse_qs

