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

