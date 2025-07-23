from flask import Flask, render_template, request, jsonify
from main import handle_command, speak, run_jarvis
import threading
import os

app = Flask(__name__)
ALWAYS_LISTENING = True
# Ensure chatlog file exists
if not os.path.exists("chatlog.txt"):
    with open("chatlog.txt", "w") as f:
        f.write("🤖 Jarvis: Hello! How can I help you today?\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"response": "I didn't get that."})

    try:
        result = handle_command(user_input)

        # Speak only short messages
        if len(result.split()) <= 6:
            threading.Thread(target=speak, args=(result,), daemon=True).start()

        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

@app.route('/toggle_listen', methods=['POST'])
def toggle_listen():
    from main import toggle_listening  # Assumes toggle function exists in main
    data = request.json
    if data and "enabled" in data:
        success = toggle_listening(data["enabled"])
        if success:
            return jsonify({"status": "ok", "always_listening": data["enabled"]})
    return jsonify({"status": "error", "message": "Invalid request"}), 400

@app.route('/chatlog', methods=['GET'])
def chatlog():
    try:
        with open("chatlog.txt", "r") as f:
            lines = f.readlines()[-10:]
        return jsonify({"messages": lines})
    except Exception as e:
        return jsonify({"messages": [f"Error reading log: {e}"]})

if __name__ == '__main__':
    if ALWAYS_LISTENING:
        threading.Thread(target=run_jarvis, daemon=True).start()
    app.run(debug=True, port=4444)
