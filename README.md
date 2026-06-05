# ha-pulse-eight-neo

Home Assistant integration for the Pulse-Eight Neo HDMI matrix switcher. Lets you control input routing and monitor system health directly from HA.

Tested on a neo:4 but should work fine on other Neo matrix models since they all use the same REST API.

## What it does

- Dropdown selector per output to switch sources
- Diagnostic sensors (system status, PSU, temperature, uptime, input/output module health)
- TX firmware version per output port
- Network connectivity sensor
- Reboot button

## Requirements

- Pulse-Eight Neo matrix on your local network with the HTTP API accessible
- Home Assistant 2026.6 or newer
- A static IP or DHCP reservation for the matrix is strongly recommended

## Installation

### HACS (recommended)

1. In HACS, go to the three-dot menu (top right) and click **Custom repositories**
2. Paste `https://github.com/codergrounds/ha-neo-pulseeight` and set the category to **Integration**, then click Add
3. Search for "Pulse-Eight Neo" in HACS and install it
4. Restart Home Assistant
5. Go to Settings → Integrations → Add Integration → search for "Pulse-Eight Neo"

### Manual

Copy the `custom_components/pulse_eight_neo` folder into your HA config's `custom_components` directory and restart.

## Setup

Just enter the IP address of your matrix when prompted. Port defaults to 80, only change it if you've set up something unusual on your network.

The integration will pull the model and serial from the device and create the entities automatically based on how many inputs/outputs are detected.

## Entities

| Entity | Type | Notes |
|---|---|---|
| Output 1, Output 2, ... | Select | Source selector per output |
| System Status | Sensor | Overall health message from the matrix |
| Power Supply | Sensor | PSU health |
| Inputs Health | Sensor | Input module status |
| Outputs Health | Sensor | Output module status |
| Temperature | Sensor | Internal temperature in °C |
| Uptime | Sensor | Seconds since last boot |
| Network Connectivity | Sensor | Online/Disconnected based on poll success |
| Output N TX Firmware | Sensor | HDBaseT transmitter firmware per output |
| Reboot System | Button | Sends a reboot command to the matrix |

## Notes

- The matrix is polled every 10 seconds
- Input/output names shown in the dropdowns come directly from the matrix
- If you rename an input and have automations using `select.select_option` with the old name, those will need updating
- The reboot button works and actually reboots the matrix, so don't press it by accident

## License

MIT
