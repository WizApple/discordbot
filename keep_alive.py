from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Discord bot is running! ✅"

@app.route('/status')
def status():
    return {"status": "online", "message": "Bot is active"}

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("🌐 Web server started on port 8080")
