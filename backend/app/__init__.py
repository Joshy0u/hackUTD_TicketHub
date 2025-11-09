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

    # --- Initialize OAuth / Auth0 ---
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
        # 👇 Redirect to the frontend root after successful login
        return redirect(f"{frontend_url}/")

    @app.route("/logout")
    def logout():
        session.clear()
        # 👇 Redirect to the frontend root after logout
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

    # --- Register blueprints ---
    from .routes.tickets import tickets
    app.register_blueprint(tickets, url_prefix="/tickets")

    return app
