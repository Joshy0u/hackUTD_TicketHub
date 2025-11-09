# app/__init__.py
import json
from urllib.parse import urlencode, quote_plus
from flask import Flask, redirect, render_template, session, url_for
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from .config import Config


def make_app():
    app = Flask("Sensor")
    app.config.from_object(Config)
    app.secret_key = app.config["SECRET_KEY"]

    frontend_url = app.config["FRONTEND_URL"]

    # Enable CORS
    CORS(app)

    # init auth0
    oauth = OAuth(app)
    oauth.register(
        "auth0",
        client_id=app.config["AUTH0_CLIENT_ID"],
        client_secret=app.config["AUTH0_CLIENT_SECRET"],
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid-configuration',
    )

    # --- Auth routes ---
    @app.route("/login")
    def login():
        return oauth.auth0.authorize_redirect(
            redirect_uri=url_for("callback", _external=True)
        )

    @app.route("/callback", methods=["GET", "POST"])
    def callback():
        token = oauth.auth0.authorize_access_token()
        session["user"] = token
        # 
        return redirect(f"{frontend_url}/dashboard")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(
            f"https://{app.config['AUTH0_DOMAIN']}/v2/logout?"
            + urlencode(
                {
                    "returnTo": f"{frontend_url}/",
                    "client_id": app.config["AUTH0_CLIENT_ID"],
                },
                quote_via=quote_plus,
            )
        )
    # The tickets module exposes the `bad_logs` blueprint (reflecting the bad_logs table)
    from .routes.tickets import bad_logs
    app.register_blueprint(bad_logs)

    return app
