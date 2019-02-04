from .application import WazuhApplication

app = WazuhApplication()
app.bootstrap()
app.run()
app.destroy()
