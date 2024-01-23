import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/webhook', methods=['GET'])
def check_paments():
    data = request.get_json()
    print(data)