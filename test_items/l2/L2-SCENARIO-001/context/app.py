from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello, World!"})

@app.route("/api/users")
def list_users():
    return jsonify({"users": []})

if __name__ == "__main__":
    app.run(debug=True)
