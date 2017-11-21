from flask import Flask
from flask_cors import CORS
from anchor_packages_training import train_anchor_packages
import flask
from read_data import read_s3_bucket

app = Flask(__name__)
# app.config.from_object('config')
CORS(app)


@app.route('/api/v1/anchor-package/train')
def train():
    return train_anchor_packages()


@app.route('/api/v1/anchor-package/get-packages')
def get_anchor_packages():
    return flask.jsonify(read_s3_bucket())


if __name__ == "__main__":
    app.run()
