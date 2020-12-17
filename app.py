import sentry_sdk

from chalice import Chalice, Rate
from chalicelib import service, settings

from sentry_sdk.integrations.chalice import ChaliceIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[ChaliceIntegration()],
    traces_sample_rate=1.0
)

app = Chalice(app_name='sensors-africa-airqo')

@app.route("/")
def run():
    app.log.debug("run")
    return service.run()

# Automatically runs every hour
@app.schedule(Rate(settings.SCHEDULE_RATE, unit=Rate.HOURS))
def periodic_task(event):
    app.log.debug(event.to_dict())
    return service.run()
