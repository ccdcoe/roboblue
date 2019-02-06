from .application import ReputationApplication

app = ReputationApplication()
app.bootstrap()
app.run()
app.destroy()
