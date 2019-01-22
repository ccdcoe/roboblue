from .application import HistorianApplication

app = HistorianApplication()

app.bootstrap()
app.run()
app.destroy()
