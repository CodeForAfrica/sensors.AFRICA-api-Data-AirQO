import settings

from chalice import Chalice
from chalicelib import service, settings

app = Chalice(app_name='sensors-africa-airqo')

@app.route("/")
def run():
    app.log.debug("run")
    return service.run(app)

# Automatically runs every 5 minutes
@app.schedule(Rate(1, unit=Rate.HOURS))
def periodic_task(event):
    app.log.debug(event.to_dict())
    return service.run(app)

