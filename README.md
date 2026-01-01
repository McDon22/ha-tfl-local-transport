# TfL Local Transport - Home Assistant Integration

A Home Assistant custom integration that provides comprehensive local transport information using the TfL Unified API and National Rail Darwin API.

## Features

- **Train Departures**: Real-time departure times from your local station
- **Filtered Departures**: Track trains to specific destinations (e.g., Grove Park to London Charing Cross)
- **Train Arrivals**: Track incoming trains to your station
- **Line Status**: Southeastern, Southern, Thameslink line status and disruptions
- **Bus Arrivals**: Real-time bus arrivals at nearby stops (via TfL API)
- **NRCC Messages**: National Rail Customer Communication messages

## Installation

### Manual Installation

1. Copy the `tfl_local_transport` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings** > **Devices & Services** > **Add Integration**
4. Search for "TfL Local Transport" and configure

### HACS Installation

1. Add this repository as a custom repository in HACS
2. Install "TfL Local Transport"
3. Restart Home Assistant
4. Configure via the UI

## Configuration

### Required Settings

| Setting | Description |
|---------|-------------|
| Station CRS | Your station's 3-letter CRS code (e.g., `GRP` for Grove Park) |

### Optional Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Darwin API Key | National Rail API key for higher rate limits | None |
| TfL API Key | TfL API key for higher rate limits | None |
| Destinations | London stations to monitor | CHX, LBG, VIC |
| Lines | Rail lines to monitor for status | Southeastern |
| Num Departures | Number of trains to show | 10 |
| Time Window | How far ahead to look (minutes) | 120 |

### Getting API Keys

**National Rail Darwin API** (recommended for reliable train data):
1. Visit https://raildata.org.uk/
2. Register for an account
3. Subscribe to the "Live Departure Board" API

**TfL API Key** (recommended for bus data):
1. Visit https://api-portal.tfl.gov.uk/
2. Register for an account
3. Create an application to get your key

**Note**: Without API keys, the integration will use community endpoints with rate limits. API keys are highly recommended for production use.

## Station CRS Codes

Common stations in the Grove Park area:

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

The integration creates the following sensors:

### Train Departures
- `sensor.train_departures_grp` - All departures from Grove Park
- `sensor.train_departures_grp_chx` - Departures to Charing Cross
- `sensor.train_departures_grp_lbg` - Departures to London Bridge
- `sensor.train_departures_grp_vic` - Departures to Victoria

### Train Arrivals
- `sensor.train_arrivals_grp` - All arrivals at Grove Park

### Line Status
- `sensor.line_status` - Current line status for monitored lines

### Bus Arrivals (if configured)
- `sensor.bus_stop_{stop_id}` - Bus arrivals at configured stops

## Sensor Attributes

### Train Departure Sensors

```yaml
station_name: "Grove Park"
crs: "GRP"
generated_at: "2025-01-01T10:30:00Z"
filter_destination: "London Charing Cross"
trains:
  - scheduled: "10:35"
    expected: "On time"
    platform: "1"
    destination: "London Charing Cross"
    operator: "Southeastern"
    is_cancelled: false
    calling_points:
      - station: "Hither Green"
        scheduled: "10:39"
      - station: "Lewisham"
        scheduled: "10:42"
```

## Example Lovelace Cards

### Simple Train Departure Card

```yaml
type: entities
title: Next Trains to London
entities:
  - entity: sensor.train_departures_grp_chx
    name: To Charing Cross
  - entity: sensor.train_departures_grp_lbg
    name: To London Bridge
  - entity: sensor.train_departures_grp_vic
    name: To Victoria
```

### Detailed Departure Board (Markdown Card)

```yaml
type: markdown
title: Grove Park Departures
content: |
  {% set trains = state_attr('sensor.train_departures_grp', 'trains') %}
  | Time | Platform | Destination | Status |
  |------|----------|-------------|--------|
  {% for train in trains[:5] %}
  | {{ train.scheduled }} | {{ train.platform }} | {{ train.destination }} | {{ train.expected }} |
  {% endfor %}
```

### Departure Board with Delays Highlighted

```yaml
type: markdown
title: Grove Park to Charing Cross
content: |
  {% set trains = state_attr('sensor.train_departures_grp_chx', 'trains') %}
  {% for train in trains[:3] %}
  **{{ train.scheduled }}** → Platform {{ train.platform or 'TBC' }}
  {% if train.is_cancelled %}
  🚫 CANCELLED{% if train.cancel_reason %}: {{ train.cancel_reason }}{% endif %}
  {% elif train.expected != 'On time' and train.expected != train.scheduled %}
  ⚠️ Expected: {{ train.expected }}{% if train.delay_reason %} ({{ train.delay_reason }}){% endif %}
  {% else %}
  ✅ On time
  {% endif %}
  
  {% endfor %}
```

### Line Status Card

```yaml
type: entities
title: Line Status
entities:
  - entity: sensor.line_status
    name: Southeastern
```

## Automations

### Notify on Train Cancellations

```yaml
automation:
  - alias: "Train Cancellation Alert"
    trigger:
      - platform: state
        entity_id: sensor.train_departures_grp_chx
    condition:
      - condition: template
        value_template: >
          {% set trains = state_attr('sensor.train_departures_grp_chx', 'trains') %}
          {{ trains | selectattr('is_cancelled', 'equalto', true) | list | count > 0 }}
    action:
      - service: notify.mobile_app
        data:
          title: "Train Cancelled"
          message: >
            {% set trains = state_attr('sensor.train_departures_grp_chx', 'trains') %}
            {% set cancelled = trains | selectattr('is_cancelled', 'equalto', true) | first %}
            The {{ cancelled.scheduled }} to {{ cancelled.destination }} has been cancelled.
```

### Morning Commute Summary

```yaml
automation:
  - alias: "Morning Commute Update"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
    action:
      - service: notify.mobile_app
        data:
          title: "Morning Commute"
          message: >
            {% set trains = state_attr('sensor.train_departures_grp_chx', 'trains') %}
            Next train: {{ trains[0].scheduled }} ({{ trains[0].expected }})
            Platform: {{ trains[0].platform or 'TBC' }}
```

## Troubleshooting

### No train data showing
- Verify your station CRS code is correct
- Check if you've exceeded API rate limits (get an API key)
- Ensure the station has services running

### "On time" not showing correctly
- The Darwin API sometimes returns the scheduled time as the expected time
- Check the `is_cancelled` and `delay_reason` attributes for more info

### API rate limiting
- Register for API keys for higher limits
- The integration updates every 2 minutes by default
- Reduce the number of monitored destinations if needed

## API Information

This integration uses:

1. **Huxley2 Community API** (default, no key needed):
   - REST JSON proxy for National Rail Darwin data
   - Rate limited, suitable for personal use

2. **Rail Data Marketplace API** (with API key):
   - Direct access to Darwin Live Departure Boards
   - Higher rate limits, more reliable

3. **TfL Unified API**:
   - Line status for Southeastern and other lines
   - Bus arrival times
   - Station information

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License
