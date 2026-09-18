from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

# Mock data for demonstration
server_time = {"hour": 12, "minute": 30, "second": 45}
telemetry_data = {}
lock_info = {}
kamikaze_info = {}
qr_coordinates = {"latitude": 41.0, "longitude": 29.0}
hss_coordinates = [{"latitude": 41.1, "longitude": 29.1}]

# Authentication mock
users = {"team": "password123"}

@app.route('/api/sunucusaati', methods=['GET'])
def get_server_time():
    return jsonify(server_time), 200

@app.route('/api/telemetri_gonder', methods=['POST'])
def post_telemetry():
    if not request.is_json:
        return make_response("Invalid format", 204)
    data = request.get_json()
    telemetry_data.update(data)
    return jsonify(telemetry_data), 200

@app.route('/api/kilitlenme_bilgisi', methods=['POST'])
def post_lock_info():
    if not request.is_json:
        return make_response("Invalid format", 204)
    data = request.get_json()
    lock_info.update(data)
    return jsonify(lock_info), 200

@app.route('/api/giris', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not (auth.username in users and users[auth.username] == auth.password):
        return make_response("Unauthorized", 401)
    return jsonify({"message": "Login successful"}), 200

@app.route('/api/kamikaze_bilgisi', methods=['POST'])
def post_kamikaze_info():
    if not request.is_json:
        return make_response("Invalid format", 204)
    data = request.get_json()
    kamikaze_info.update(data)
    return jsonify(kamikaze_info), 200

@app.route('/api/qr_koordinati', methods=['GET'])
def get_qr_coordinates():
    return jsonify(qr_coordinates), 200

@app.route('/api/hss_koordinatlari', methods=['GET'])
def get_hss_coordinates():
    return jsonify(hss_coordinates), 200

@app.errorhandler(404)
def not_found(error):
    return make_response("Invalid URL", 404)

@app.errorhandler(500)
def server_error(error):
    return make_response("Internal server error", 500)

if __name__ == '__main__':
    app.run(debug=True)