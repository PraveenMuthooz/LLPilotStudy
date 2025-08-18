import dash
from dash import dcc, html, Dash
from dash.dependencies import Input, Output, State
import dash_mantine_components as dmc
from dash import page_container
from dash_iconify import DashIconify
import webbrowser
from threading import Timer
from cache_config import init_cache


app = Dash("Living Lab Pilot Study", use_pages=True, suppress_callback_exceptions=True)
init_cache(app.server)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:{}".format(8050))

def get_icon(icon):
    return DashIconify(icon=icon, height=16)

app_shell = dmc.AppShell(
     [
          dmc.AppShellHeader(
               dmc.Group(
                    [
                         dmc.Burger(
                              id="burger",
                              opened=False,  # Start closed
                          ),
                          dmc.Title("LIVING LAB PILOT PROJECT", c="midnightblue", size="h1", style = {'marginLeft': 'auto'}),
                          dmc.Group(
                                [
                                      dmc.Image(src='./assets/Physical_Internet_Center_GTGold_RGB.png', h=40, flex=0),
                                      dmc.Image(src='./assets/SCL_Logo.png', h=70, flex=0),
                                ],
                                style={"marginLeft": "auto"},
                          ),
                    ],
                    h="100%",
                    px="xs",
             ), style={"backgroundColor":"turquoise", 'zIndex': 2050}, 
       ),
       dmc.AppShellNavbar(
             id="navbar",
             children=[
                    dmc.NavLink(
                              label=page["name"],
                              href=page["path"],
                              variant="filled",
                              active=True,
                              leftSection = get_icon(icon='bi:truck-front-fill'),
                              rightSection= get_icon(icon='bi:chevron-right'),
                              )
                    for page in dash.page_registry.values()
           ],
          p=0,
          maw=300,
   ),
   dmc.AppShellMain(page_container),
 ],
header={
          "height": {"base": 0, "md": 60, "lg": 70},
     },
navbar={
     "width": {"base": 50, "md": 100, "lg": 300},
     "breakpoint": "sm",  # Set a smaller breakpoint
     "collapsed": {"mobile": True, "desktop": True},  # Start collapsed
},
padding="xs",
id="appshell"
)

app.layout = dmc.MantineProvider(app_shell)

@app.callback(
     Output("appshell", "navbar"),
     Input("burger", "opened"),
     prevent_initial_call=True,
)
def toggle_navbar(opened):
     new_navbar = {
          "width": {"base": 200, "md": 300, "lg": 400},
          "breakpoint": "sm",
          "collapsed": {"mobile": not opened, "desktop": not opened},
     }
     return new_navbar

if __name__ == "__main__":
     Timer(1, open_browser).start()  # Open browser after 1 second
     app.run(debug=False)