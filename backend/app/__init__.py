from flask import Flask
from flask_cors import CORS

def make_app():
  app = Flask("Sensor")

  CORS(app)

  from .routes.tickets import tickets
  app.register_blueprint(tickets, url_prefix='/tickets')

  return app