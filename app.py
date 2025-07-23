# main.py
# (Your BeautifulSoup + requests scraping functions here)
# def scrape_hindustan():
#     ...

from flask import Flask, jsonify
from flask_cors import CORS  # Optional, only needed if you want CORS

app = Flask(__name__)
CORS(app)  # Comment out if you don't need CORS

@app.route('/')
def home():
    return "The Hindustan Times scraper API is running! Use /data to get results."

@app.route('/data')
def get_data():
    from main import scrape_hindustan
    try:
        results = scrape_hindustan()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)