from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "OK: Success"}), 200


from routes import login
from routes import user
from routes import follows
from routes import followers
from routes import tweets
from routes import tweetLikes
from routes import comments
from routes import commentLikes
