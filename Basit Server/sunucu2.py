from flask import Flask, request, jsonify, make_response, json
import datetime

app = Flask(__name__)

telemetry_data = {}  # Dictionary to store telemetry data with timestamps

@app.route('/api/telemetri_gonder', methods=['POST'])
def post_telemetry():
    try:
        data = request.get_json()
        drone_name = data.get("drone_name", "Unknown Drone")
        telemetry = data.get("telemetry")

        timestamp = datetime.datetime.now().isoformat()  # Get current timestamp

        # Store telemetry data with timestamp
        if drone_name not in telemetry_data:  # <--- Fix here
            telemetry_data[drone_name] = {}
        telemetry_data[drone_name][timestamp] = telemetry


        print(f"Received telemetry from {drone_name} at {timestamp}:")
        print(json.dumps(telemetry, indent=4))

        return jsonify({"message": "Telemetry data received and stored successfully!"}), 200

    except Exception as e:
        print(f"Error processing telemetry: {e}")
        return jsonify({"error": "An error occurred while processing the data."}), 500


@app.route('/api/telemetri_al', methods=['GET'])
def get_telemetry():
    try:
        return jsonify(telemetry_data), 200  # Return all stored telemetry data
    except Exception as e:
        print(f"Error retrieving telemetry: {e}")
        return jsonify({"error": "An error occurred while retrieving the data."}), 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')