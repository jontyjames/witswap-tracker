from flask import Flask, render_template, jsonify, request
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DATABASE = 'marine_data.db'
TARGET_URL = os.environ.get(
    'WITSWAP_TARGET_URL',
    'https://ponlapp.napierport.co.nz/witswap/(S(ex0x45wlnknfzxkdhdi1nbzr))/MobileWebForm1.aspx'
)
NZ_TZ = ZoneInfo('Pacific/Auckland')

# Scraper status tracking
scraper_status = {
    'last_success': None,
    'last_attempt': None,
    'last_error': None,
    'consecutive_errors': 0,
    'total_fetches': 0,
    'total_errors': 0,
}


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
    """Scrape data from the target webpage with retry logic"""
    max_attempts = 3
    retry_delay = 5

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(TARGET_URL, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            data = {}
            list_items = soup.find_all('li')

            if not list_items:
                logger.warning("No <li> elements found on page (attempt %d/%d)", attempt, max_attempts)
                if attempt < max_attempts:
                    time.sleep(retry_delay)
                    continue
                return None

            for item in list_items:
                text = item.get_text(strip=True)

                if ':' in text:
                    label, value = text.split(':', 1)
                    label = label.strip()
                    value = value.strip()

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

            if 'date' in data and 'time' in data:
                data['timestamp'] = f"{data['date']} {data['time']}"

            data['recorded_at'] = datetime.now(NZ_TZ).isoformat()

            logger.info("Scraped data successfully: %s", data.get('timestamp', 'no timestamp'))
            return data

        except (Timeout, ConnectionError) as e:
            logger.warning("Network error on attempt %d/%d: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(retry_delay)
                continue
            return None
        except HTTPError as e:
            logger.warning("HTTP error on attempt %d/%d: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(retry_delay)
                continue
            return None
        except Exception as e:
            logger.error("Unexpected error scraping data: %s", e)
            return None

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
        cutoff_time = (datetime.now(NZ_TZ) - timedelta(days=2)).isoformat()
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('DELETE FROM marine_data WHERE recorded_at < ?', (cutoff_time,))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        logger.info("Cleaned up %d old records (older than 2 days)", deleted)
        return deleted
    except Exception as e:
        logger.error("Error cleaning up old data: %s", e)
        return 0


def scheduled_fetch():
    """Scheduled task to fetch data automatically"""
    scraper_status['last_attempt'] = datetime.now(NZ_TZ).isoformat()
    scraper_status['total_fetches'] += 1

    data = scrape_data()
    if data and save_data(data):
        scraper_status['last_success'] = datetime.now(NZ_TZ).isoformat()
        scraper_status['consecutive_errors'] = 0
        scraper_status['last_error'] = None
        logger.info("Data saved successfully")
    else:
        scraper_status['consecutive_errors'] += 1
        scraper_status['total_errors'] += 1
        scraper_status['last_error'] = datetime.now(NZ_TZ).isoformat()
        logger.warning("Failed to fetch/save data (consecutive errors: %d)", scraper_status['consecutive_errors'])


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/fetch', methods=['POST'])
def fetch_data():
    """API endpoint to manually fetch and store data"""
    data = scrape_data()
    if data and save_data(data):
        scraper_status['last_success'] = datetime.now(NZ_TZ).isoformat()
        scraper_status['consecutive_errors'] = 0
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


@app.route('/api/data/averaged')
def get_averaged_data():
    """API endpoint to retrieve 10-minute averaged data with max envelope"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM marine_data ORDER BY id ASC')
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    if not rows:
        return jsonify([])

    # Group into 10-minute buckets based on recorded_at
    buckets = {}
    for row in rows:
        ra = row.get('recorded_at', '')
        try:
            dt = datetime.fromisoformat(ra)
        except (ValueError, TypeError):
            continue
        # Round down to nearest 10 minutes
        bucket_key = dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0).isoformat()
        buckets.setdefault(bucket_key, []).append(row)

    numeric_fields = [
        'spur_speed', 'spur_direction', 'spur_gust',
        'clarke_speed', 'clarke_direction', 'clarke_gust',
        'tide_height', 'wave_height', 'wave_direction', 'peak_period',
        'w1', 'w6m'
    ]

    result = []
    for bucket_key in sorted(buckets.keys()):
        group = buckets[bucket_key]
        entry = {'bucket': bucket_key}
        # Carry forward the timestamp from the last row in the bucket for label display
        entry['timestamp'] = group[-1].get('timestamp', '')
        entry['recorded_at'] = bucket_key

        for field in numeric_fields:
            values = [r[field] for r in group if r.get(field) is not None]
            if values:
                entry[f'{field}_avg'] = round(sum(values) / len(values), 2)
                entry[f'{field}_max'] = round(max(values), 2)
            else:
                entry[f'{field}_avg'] = None
                entry[f'{field}_max'] = None

        result.append(entry)

    return jsonify(result)


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


@app.route('/api/status')
def get_status():
    """API endpoint to get scraper health status"""
    health = 'healthy'
    if scraper_status['consecutive_errors'] >= 5:
        health = 'unhealthy'
    elif scraper_status['consecutive_errors'] >= 2:
        health = 'degraded'

    return jsonify({
        'health': health,
        'last_success': scraper_status['last_success'],
        'last_attempt': scraper_status['last_attempt'],
        'last_error': scraper_status['last_error'],
        'consecutive_errors': scraper_status['consecutive_errors'],
        'total_fetches': scraper_status['total_fetches'],
        'total_errors': scraper_status['total_errors'],
    })


# Initialize database and scheduler at module level so gunicorn picks them up
init_db()

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_fetch, trigger="interval", minutes=2, id='fetch_data')
scheduler.add_job(func=cleanup_old_data, trigger="interval", hours=1, id='cleanup_data')
scheduler.start()
logger.info("Scheduler started: fetching every 2 min, cleanup every 1 hr")

# Fetch initial data
logger.info("Fetching initial data...")
scheduled_fetch()

atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port, use_reloader=False)
