from flask import Flask
from flask_cors import CORS
from .consumer import start_consumer

def make_app():
  app = Flask("Sensor")

  CORS(app)

  from .routes.sensors import sensors
  app.register_blueprint(sensors)

  start_consumer()

  return app