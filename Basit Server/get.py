import requests
import json
import datetime

def get_and_save_telemetry(server_url, output_filename="telemetry.json"):
    try:
        response = requests.get(server_url)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        telemetry_data = response.json()

        # Add a timestamp to the saved data (optional but recommended)
        current_time = datetime.datetime.now().isoformat()
        telemetry_data["_retrieved_at"] = current_time


        with open(output_filename, 'w') as f:
            json.dump(telemetry_data, f, indent=4)  # Save with pretty printing
        print(f"Telemetry data saved to {output_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Error retrieving telemetry: {e}")
    except Exception as e:
        print(f"Error saving telemetry: {e}")



if __name__ == "__main__":
    server_address = "http://0.0.0.0:5000/api/telemetri_al"  # Replace with your server address
    get_and_save_telemetry(server_address)