# NRC Nuclear Reactor Status Data Scraper

A comprehensive tool for scraping, storing, and analyzing historical nuclear reactor status data from the U.S. Nuclear Regulatory Commission (NRC).

## Features

- **Historical Data Collection**: Scrape daily reactor status reports from 1999-2025
- **SQLite Database Storage**: Automatically store data in a structured database
- **Resume Capability**: Continue scraping from where you left off
- **Data Analysis Tools**: Built-in analysis and visualization capabilities
- **Respectful Scraping**: Configurable delays to be respectful to NRC servers
- **Error Handling**: Robust error handling and logging
- **Multiple Database Support**: Create separate databases for different datasets

## Installation

1. **Clone or download the project files**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Option 1: Interactive Menu (Recommended for Beginners)
```bash
python scrape_nrc_data.py
```
This will show you a menu with options to:
- Scrape recent data (2025 only)
- Scrape sample years (2020-2022) 
- Scrape all historical data (1999-2025)
- View database statistics

### Option 2: Command Line (Advanced Users)
```bash
# Scrape all historical data (1999-2025)
python nrc_data_scraper.py

# Scrape specific years
python nrc_data_scraper.py --start-year 2020 --end-year 2022

# Resume from a specific date
python nrc_data_scraper.py --resume-from 20220515

# Use custom database and delay
python nrc_data_scraper.py --db-path my_data.db --delay 2.0

# Show database statistics only
python nrc_data_scraper.py --stats-only
```

## Database Schema

The data is stored in a SQLite database with the following structure:

```sql
CREATE TABLE reactor_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,              -- YYYYMMDD format
    year INTEGER NOT NULL,           -- Year extracted from date
    region TEXT,                     -- NRC Region (Region 1, Region 2, etc.)
    unit_name TEXT NOT NULL,         -- Reactor name (e.g., "Beaver Valley 1")
    power_level INTEGER,             -- Power level percentage (0-100)
    down_date TEXT,                  -- Date reactor went down (if applicable)
    reason_comment TEXT,             -- Reason for reduced power/outage
    change_indicator TEXT,           -- "*" if changed in past 24 hours
    scrams_count TEXT,               -- Number of scrams in past 24 hours
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Data Analysis

### Basic Analysis
```bash
# Analyze all data
python analyze_nrc_data.py

# Analyze specific reactor
python analyze_nrc_data.py --reactor "Beaver Valley 1"

# Generate plots
python analyze_nrc_data.py --plots

# Export summary report
python analyze_nrc_data.py --export
```

### Using in Python Scripts
```python
from analyze_nrc_data import NRCDataAnalyzer

# Load and analyze data
analyzer = NRCDataAnalyzer("nrc_reactor_data.db")
analyzer.basic_stats()
analyzer.outage_analysis()
analyzer.power_level_trends()
```

## Example Analyses You Can Perform

1. **Reactor Performance Tracking**: Monitor individual reactor performance over time
2. **Outage Pattern Analysis**: Identify common outage reasons and seasonal patterns
3. **Capacity Factor Calculations**: Calculate fleet-wide capacity factors by year
4. **Regional Comparisons**: Compare performance across different NRC regions
5. **Maintenance Scheduling**: Analyze when reactors typically go offline for maintenance
6. **Economic Dispatch**: Study reduced power operations for economic reasons

## Important Notes

### Data Availability
- NRC reports are typically published Monday-Friday (weekends are skipped)
- Some dates may not have reports available
- Data format and availability may vary for older years (1999-2005)

### Respectful Usage
- Default delay is 1 second between requests
- Increase delay if you encounter rate limiting
- The NRC website is a government resource - be respectful

### Data Quality
- Data is scraped "as-is" from NRC reports
- Some historical data may have formatting inconsistencies
- Always validate critical analyses with official NRC sources

## Performance Estimates

Scraping the complete historical dataset (1999-2025):
- **Total dates**: ~6,800 weekdays
- **Estimated time**: 2-3 hours (at 1 second delay)
- **Database size**: ~50-100 MB
- **Total records**: ~500,000-1,000,000

## Troubleshooting

### Common Issues

1. **Network timeouts**: Increase the `--delay` parameter
2. **Missing lxml**: Install with `pip install lxml`
3. **Database locked**: Make sure no other process is using the database
4. **Memory issues**: For large datasets, consider processing data in chunks

### Error Logs
Check `nrc_scraper.log` for detailed error information.

## File Structure

```
├── nrc_data_scraper.py     # Main scraper class and CLI
├── scrape_nrc_data.py      # Interactive menu interface
├── analyze_nrc_data.py     # Data analysis tools
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── nrc_scraper.log        # Scraping log file
└── *.db                   # SQLite database files
```

## Sample Data Points

The scraper captures data like:
- **Beaver Valley 1**: 100% power, no outages
- **Millstone 3**: 0% power, down since 4/11/2025 for refueling outage
- **Hope Creek 1**: 88% power, reduced for maintenance
- **Vogtle 4**: 30% power, reduced for maintenance

## Contributing

Feel free to submit issues or pull requests to improve the scraper:
- Add support for additional data fields
- Improve error handling
- Add new analysis features
- Optimize scraping performance

## Legal Notice

This tool scrapes publicly available data from the NRC website. Always:
- Respect the NRC's website terms of use
- Use reasonable delays between requests
- Cite the NRC as the data source in any publications
- Verify critical information with official NRC sources

## Data Source

Original data source: [NRC Power Reactor Status Reports](https://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/)

---

*This tool is not affiliated with or endorsed by the U.S. Nuclear Regulatory Commission.* 