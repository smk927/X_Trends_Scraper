import os
from flask import Flask, render_template, jsonify
from datetime import datetime
from src.scraper import TwitterScraper

app = Flask(__name__,
            template_folder=os.path.abspath('templates'),
            static_folder=os.path.abspath('static'))

scraper = TwitterScraper()


@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Template error: {str(e)}")
        return str(e), 500


@app.route('/run-scraper')
def run_scraper():
    try:
        result = scraper.get_trending_topics()

        if isinstance(result['timestamp'], str):
            try:
                result['timestamp'] = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                result['timestamp'] = datetime.now()

        result['timestamp'] = result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        required_fields = ['nameoftrend1', 'nameoftrend2', 'nameoftrend3',
                           'nameoftrend4', 'nameoftrend5', 'ip_address']

        for field in required_fields:
            if field not in result:
                result[field] = 'N/A'

        return jsonify(result)
    except Exception as e:
        error_response = {
            "error": str(e),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "nameoftrend1": "Error fetching trend",
            "nameoftrend2": "Error fetching trend",
            "nameoftrend3": "Error fetching trend",
            "nameoftrend4": "Error fetching trend",
            "nameoftrend5": "Error fetching trend",
            "ip_address": "N/A"
        }
        return jsonify(error_response), 500


if __name__ == '__main__':
    app.run(debug=True)