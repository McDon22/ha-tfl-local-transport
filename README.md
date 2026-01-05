<p align="center">
  <img src="logo.png" alt="TfL Local Transport" width="200">
</p>

<h1 align="center">TfL Local Transport</h1>
<p align="center">
  <strong>A Home Assistant integration for local transport information</strong>
</p>

<p align="center">
  <a href="https://github.com/McDon22/ha-tfl-local-transport/releases"><img src="https://img.shields.io/github/v/release/McDon22/ha-tfl-local-transport?style=flat-square" alt="Release"></a>
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square" alt="HACS Custom"></a>
  <img src="https://img.shields.io/github/license/McDon22/ha-tfl-local-transport?style=flat-square" alt="License">
</p>

---

A Home Assistant custom integration that provides comprehensive local transport information using the TfL Unified API and National Rail Darwin API.

## Features

- **Train Departures**: Real-time departure times from your local station
- **Filtered Departures**: Track trains to specific destinations (e.g., Grove Park to London Charing Cross)
- **Train Arrivals**: Track incoming trains to your station
- **Line Status**: Southeastern, Southern, Thameslink line status and disruptions
- **Bus Arrivals**: Real-time bus arrivals at nearby stops (via TfL API)
- **NRCC Messages**: National Rail Customer Communication messages
- **Darwin API Support**: Direct connection to Rail Data Marketplace with automatic Huxley fallback

## Installation

### HACS Installation (Recommended)

1. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ (menu) → Custom repositories
   - Add `https://github.com/McDon22/ha-tfl-local-transport`
   - Category: Integration
2. Install "TfL Local Transport"
3. Restart Home Assistant
4. Configure via the UI

### Manual Installation

1. Copy the `custom_components/tfl_local_transport` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings** > **Devices & Services** > **Add Integration**
4. Search for "TfL Local Transport" and configure

## Configuration

### Required Settings

| Setting | Description |
|---------|-------------|
| Station CRS | Your station's 3-letter CRS code (e.g., `GRP` for Grove Park) |

### Optional Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Darwin API Key | National Rail API key (highly recommended) | None |
| TfL API Key | TfL API key for bus data | None |
| Destinations | London stations to monitor | CHX, LBG, VIC |
| Lines | Rail lines to monitor for status | Southeastern |
| Num Departures | Number of trains to show | 10 |
| Time Window | How far ahead to look (minutes) | 120 |

### Getting API Keys

**National Rail Darwin API** (highly recommended):
1. Visit https://raildata.org.uk/
2. Register for an account
3. Subscribe to the "Live Departure Board" API
4. Use the Consumer Key as your Darwin API key

**TfL API Key** (recommended for bus data):
1. Visit https://api-portal.tfl.gov.uk/
2. Register for an account
3. Create an application to get your key

## Station CRS Codes

Common stations:

| Station | CRS Code |
|---------|----------|
| Grove Park | GRP |
| Hither Green | HGR |
| Lee | LEE |
| Lewisham | LEW |
| Blackheath | BKH |
| London Bridge | LBG |
| London Charing Cross | CHX |
| London Cannon Street | CST |
| London Victoria | VIC |

Find your station code at: https://www.nationalrail.co.uk/stations/

## Sensors Created

### Train Departures
- `sensor.train_departures_{crs}` - All departures from your station
- `sensor.train_departures_{crs}_{dest}` - Departures to specific destinations

### Train Arrivals
- `sensor.train_arrivals_{crs}` - All arrivals at your station

### Line Status
- `sensor.line_status` - Current line status for monitored lines

### Bus Arrivals
- `sensor.bus_stop_{stop_id}` - Bus arrivals at configured stops

## Example Lovelace Card

```yaml
type: markdown
title: Next Trains
content: |
  {% set trains = state_attr('sensor.train_departures_grp_chx', 'trains') %}
  {% for train in trains[:3] %}
  **{{ train.scheduled }}** → Platform {{ train.platform or 'TBC' }}
  {% if train.is_cancelled %}🚫 CANCELLED
  {% elif train.expected != 'On time' %}⚠️ {{ train.expected }}
  {% else %}✅ On time{% endif %}
  {% endfor %}
```

## API Information

This integration uses:

1. **Rail Data Marketplace API** (with Darwin API key):
   - Direct access to National Rail Darwin Live Departure Boards
   - Most reliable option

2. **Huxley2 Community API** (fallback):
   - REST JSON proxy for Darwin data
   - Used when Darwin API unavailable

3. **TfL Unified API**:
   - Line status information
   - Bus arrival times

## Troubleshooting

### Sensors showing "unknown"
- Verify your Darwin API key is correct
- Check Home Assistant logs for API errors
- Ensure your station CRS code is valid

### Rate limiting
- Get API keys for higher limits
- The integration updates every 2 minutes

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License
