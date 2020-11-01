"""Main app"""

# Retic
from retic import App as app

# Settings
import settings

# Routes
from routes.routes import router

# Add routes
app.use(router)


def application(req, res):
    """Deploying and hosting

    We use the application from the App class, it's use for passenger_wsgi.py
    """
    return app.application(req, res)


if __name__ == "__main__":
    # Create web server
    app.listen(
        # use_reloader=True,
        # use_debugger=True,
        hostname=app.env('APP_HOSTNAME', "localhost"),
        port=app.env.int('APP_PORT', 1801),
    )
