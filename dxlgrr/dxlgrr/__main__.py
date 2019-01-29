from .application import GRRApplication

app = GRRApplication()
app.bootstrap()
app.run()
app.destroy()
