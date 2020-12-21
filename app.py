import sentry_sdk

from chalice import Chalice, Rate
from chalicelib.service import run
from chalicelib.settings import SCHEDULE_RATE, SENTRY_DSN

from sentry_sdk.integrations.chalice import ChaliceIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[ChaliceIntegration()],
    traces_sample_rate=1.0
)

app = Chalice(app_name='sensors-africa-airqo')

# @app.route("/")
# def run():
#     app.log.debug("run")
#     return service.run(app)

# Automatically runs every hour
@app.schedule(Rate(int(SCHEDULE_RATE), unit=Rate.MINUTES))
def periodic_task(event):
    app.log.debug(event.to_dict())
    run(app)
