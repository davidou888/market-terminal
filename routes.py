from flask import Flask, request, jsonify



api = Flask(__name__)

@api.route("/get-info", methods=["GET"])
def get_info():
    result = {"[DATA]:": "those are infos!"}
    return jsonify(result)

@api.route("/post-info", methods=["POST"])
def post_info():
    data = request.json
    result = {"received": data}
    return jsonify(result)