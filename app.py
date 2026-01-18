from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timedelta
import re
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

app = Flask(__name__)
DATABASE = 'marine_data.db'
TARGET_URL = 'https://ponlapp.napierport.co.nz/witswap/(S(ex0x45wlnknfzxkdhdi1nbzr))/MobileWebForm1.aspx'

def init_db():
    """Initialize the database with the marine_data table"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS marine_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  buoy_id TEXT,
                  spur_speed REAL,
                  spur_direction REAL,
                  spur_gust REAL,
                  clarke_speed REAL,
                  clarke_direction REAL,
                  clarke_gust REAL,
                  tide_height REAL,
                  wave_height REAL,
                  wave_direction REAL,
                  peak_period REAL,
                  w1 REAL,
                  w6m REAL,
                  recorded_at TEXT)''')
    conn.commit()
    conn.close()

def extract_number(text):
    """Extract number from text, return None if not found"""
    if not text:
        return None
    match = re.search(r'[-+]?\d*\.?\d+', text.strip())
    return float(match.group()) if match else None

def scrape_data():
    """Scrape data from the target webpage"""
    try:
        response = requests.get(TARGET_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract data from the page - it's in <li> elements, not tables
        data = {}

        # Find all list items
        list_items = soup.find_all('li')

        # Parse each list item (format is "Label: Value")
        for item in list_items:
            text = item.get_text(strip=True)

            if ':' in text:
                label, value = text.split(':', 1)
                label = label.strip()
                value = value.strip()

                # Extract specific fields
                if 'Date' in label:
                    data['date'] = value
                elif 'Time' in label:
                    data['time'] = value
                elif 'Buoy ID' in label:
                    data['buoy_id'] = value
                elif 'Wind Speed (Spur)' in label:
                    data['spur_speed'] = extract_number(value)
                elif 'Wind Direct (Spur)' in label:
                    data['spur_direction'] = extract_number(value)
                elif 'Max Gust (Spur)' in label:
                    data['spur_gust'] = extract_number(value)
                elif 'Wind Speed (Clarke' in label:
                    data['clarke_speed'] = extract_number(value)
                elif 'Wind Direct (Clarke' in label:
                    data['clarke_direction'] = extract_number(value)
                elif 'Max Gust (Clarke' in label:
                    data['clarke_gust'] = extract_number(value)
                elif 'Tide Height' in label:
                    data['tide_height'] = extract_number(value)
                elif 'Sig Wave' in label:
                    data['wave_height'] = extract_number(value)
                elif 'Mean Direct' in label:
                    data['wave_direction'] = extract_number(value)
                elif 'Peak Period' in label:
                    data['peak_period'] = extract_number(value)
                elif 'Infragravity W1' in label:
                    data['w1'] = extract_number(value)
                elif 'Infragravity W6M' in label:
                    data['w6m'] = extract_number(value)

        # Combine date and time for timestamp
        if 'date' in data and 'time' in data:
            data['timestamp'] = f"{data['date']} {data['time']}"

        data['recorded_at'] = datetime.now().isoformat()

        print(f"Scraped data: {data}")  # Debug output
        return data
    except Exception as e:
        print(f"Error scraping data: {e}")
        return None

def save_data(data):
    """Save scraped data to the database"""
    if not data:
        return False

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO marine_data
                 (timestamp, buoy_id, spur_speed, spur_direction, spur_gust,
                  clarke_speed, clarke_direction, clarke_gust, tide_height,
                  wave_height, wave_direction, peak_period, w1, w6m, recorded_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('timestamp'), data.get('buoy_id'),
               data.get('spur_speed'), data.get('spur_direction'), data.get('spur_gust'),
               data.get('clarke_speed'), data.get('clarke_direction'), data.get('clarke_gust'),
               data.get('tide_height'), data.get('wave_height'), data.get('wave_direction'),
               data.get('peak_period'), data.get('w1'), data.get('w6m'),
               data.get('recorded_at')))
    conn.commit()
    conn.close()
    return True

def cleanup_old_data():
    """Remove data older than 2 days"""
    try:
        cutoff_time = (datetime.now() - timedelta(days=2)).isoformat()
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('DELETE FROM marine_data WHERE recorded_at < ?', (cutoff_time,))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        print(f"Cleaned up {deleted} old records (older than 2 days)")
        return deleted
    except Exception as e:
        print(f"Error cleaning up old data: {e}")
        return 0

def scheduled_fetch():
    """Scheduled task to fetch data automatically"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto-fetching data...")
    data = scrape_data()
    if data and save_data(data):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data saved successfully")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to fetch/save data")

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/fetch', methods=['POST'])
def fetch_data():
    """API endpoint to manually fetch and store data"""
    data = scrape_data()
    if data and save_data(data):
        return jsonify({'success': True, 'data': data})
    return jsonify({'success': False, 'error': 'Failed to fetch data'}), 500

@app.route('/api/data')
def get_data():
    """API endpoint to retrieve historical data"""
    limit = request.args.get('limit', 100, type=int)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM marine_data ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append(dict(row))

    return jsonify(data[::-1])  # Reverse to get chronological order

@app.route('/api/latest')
def get_latest():
    """API endpoint to get the most recent data point"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM marine_data ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify(dict(row))
    return jsonify(None)

if __name__ == '__main__':
    # Initialize database
    init_db()

    # Initialize scheduler
    scheduler = BackgroundScheduler()

    # Schedule data fetching every 2 minutes
    scheduler.add_job(func=scheduled_fetch, trigger="interval", minutes=2, id='fetch_data')

    # Schedule cleanup every hour to remove data older than 2 days
    scheduler.add_job(func=cleanup_old_data, trigger="interval", hours=1, id='cleanup_data')

    # Start the scheduler
    scheduler.start()
    print("Scheduler started:")
    print("  - Fetching data every 2 minutes")
    print("  - Cleaning up data older than 2 days every hour")

    # Fetch initial data
    print("Fetching initial data...")
    scheduled_fetch()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port, use_reloader=False)
