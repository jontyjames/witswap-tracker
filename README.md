# Witswap Marine Data Tracker

A web application to track and visualize marine data from the Port of Napier WITS monitoring system.

## Features

- **Automatic data collection every 2 minutes**
- **Automatic data retention for 2 days** (older data is removed automatically)
- Real-time data scraping from the Port of Napier marine monitoring page
- SQLite database for storing historical data
- Beautiful web interface with live graphs
- Tracks wind speed, direction, tide height, wave data, and more
- Interactive charts using Chart.js

## Installation

1. Make sure you have Python 3.7+ installed

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python app.py
```

The application will:
- Immediately fetch initial data
- Start automatic data collection every 2 minutes
- Automatically clean up data older than 2 days every hour

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. The web interface will display:
   - Current marine conditions
   - Historical graphs for the past 2 days
   - You can also click "Fetch Data Now" to manually trigger data collection

4. Leave the application running in the background to continuously collect data every 2 minutes

## Data Tracked

- **Wind Data (2 stations):**
  - Spur: Speed, Direction, Max Gust
  - Clarke's Corner: Speed, Direction, Max Gust

- **Tidal & Wave Data:**
  - Tide Height
  - Significant Wave Height
  - Mean Wave Direction
  - Peak Period
  - Infragravity Wave measurements

- **Metadata:**
  - Timestamp
  - Buoy ID

## Automatic Data Collection

The application automatically collects data every 2 minutes once started. You don't need to do anything!

### How it works:
- **Automatic Fetching**: Data is fetched every 2 minutes from the marine monitoring page
- **Automatic Cleanup**: Data older than 2 days is automatically deleted every hour
- **Data Retention**: You'll always have up to 2 days of historical data for tracking trends

### Console Output:
When running, you'll see messages like:
```
[2026-01-15 22:56:00] Auto-fetching data...
[2026-01-15 22:56:01] Data saved successfully
```

This confirms data is being collected automatically.

## Database

Data is stored in `marine_data.db` (SQLite database) in the same directory as the application.

## API Endpoints

- `GET /` - Main web interface
- `POST /api/fetch` - Manually trigger data fetch
- `GET /api/data?limit=100` - Get historical data (default 100 records)
- `GET /api/latest` - Get most recent data point

## Notes

- The source URL uses ASP.NET session IDs which may expire. If scraping fails, you may need to update the URL in `app.py`
- Data is displayed in chronological order in the graphs
- The web interface auto-loads historical data on page load
- Data is automatically retained for 2 days, giving you 1,440 data points (one every 2 minutes for 48 hours)
- Keep the application running continuously to maintain data collection

## Troubleshooting

If data fetching fails:
1. Check that the source website is accessible
2. Verify the URL in `app.py` is current
3. Check the console for error messages
4. The HTML structure of the source page may have changed - adjust the scraping logic in the `scrape_data()` function

## License

Free to use and modify as needed.
