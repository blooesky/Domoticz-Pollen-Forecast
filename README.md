# Domoticz Pollen Forecast Plugin

A lightweight multilingual Domoticz plugin for monitoring airborne pollen levels using the free **Open-Meteo Air Quality API**.

The plugin provides pollen alerts for **today** and **tomorrow**, together with detailed pollen information for each supported pollen type.

No API key, installer, virtual environment or external Python packages are required.

Repository: `https://github.com/blooesky/Domoticz-Pollen-Forecast`

## Features

- Free Open-Meteo Air Quality API
- No API key required
- No external Python dependencies
- No installer required
- 9 interface languages
- Configurable latitude and longitude
- Configurable update interval
- Separate pollen forecast for today and tomorrow
- Domoticz Alert sensors suitable for automations and notifications
- Detailed pollen information using Text sensors
- Keeps the last valid values if the API is temporarily unavailable

## Supported languages

- English
- Română
- Deutsch
- Français
- Italiano
- Español
- Português
- Nederlands
- Polski

The selected language controls device names when devices are first created, pollen names, alert texts and detailed Text sensor values.

## Supported pollen types

- Alder
- Birch
- Grass
- Mugwort
- Olive
- Ragweed

Pollen names are automatically translated into the selected language.

## Devices

The plugin creates four Domoticz devices:

1. **Pollen Alert Today** — Alert sensor with only the overall level for today.
2. **Pollen Alert Tomorrow** — Alert sensor with only the overall level for tomorrow.
3. **Pollen Today** — Text sensor containing the level of every supported pollen type today.
4. **Pollen Tomorrow** — Text sensor containing the level of every supported pollen type tomorrow.

Device names are translated according to the selected language when the devices are created.

## Alert levels

The Alert sensors intentionally contain **only the overall pollen level**, without the pollen type. This makes them easy to use in Domoticz automations and notifications.

The numeric `nValue` is language-independent:

| nValue | Meaning |
|---:|---|
| 0 | No data |
| 1 | None |
| 2 | Low |
| 3 | Medium |
| 4 | High |

For example, an automation can trigger when:

```text
nValue >= 3
```

This means the overall pollen level is **Medium or High**, regardless of the selected display language.

## How the daily alert is calculated

For each pollen type, the plugin takes the **highest hourly concentration** forecast for that day and converts it to one of four concentration classes.

The overall Alert sensor then uses the highest level found among all supported pollen types.

| Pollen family/type | None | Low | Medium | High |
|---|---:|---:|---:|---:|
| Alder, Birch | < 1 | 1–16 | >16–50 | >50 |
| Grass | < 1 | 1–10 | >10–30 | >30 |
| Mugwort, Ragweed | < 1 | 1–5 | >5–25 | >25 |
| Olive | < 1 | 1–5 | >5–25 | >25 |

Units are pollen grains per cubic metre (`grains/m³`). These are concentration classes, not a personalized medical allergy-risk score.

## Installation

Go to the Domoticz plugins directory:

```bash
cd /home/pi/domoticz/plugins
```

Clone the repository:

```bash
git clone https://github.com/blooesky/Domoticz-Pollen-Forecast.git PollenForecast
```

Restart Domoticz:

```bash
sudo systemctl restart domoticz
```

Then open **Setup → Hardware** and add **Pollen Forecast**.

## Manual installation

You can also download the repository and copy the folder to:

```text
/home/pi/domoticz/plugins/PollenForecast/
```

Then restart Domoticz.

## Update

If the plugin was installed using Git:

```bash
cd /home/pi/domoticz/plugins/PollenForecast
git pull
sudo systemctl restart domoticz
```

Existing devices and plugin settings are preserved during normal updates.

## Configuration

Available settings:

- **Latitude**
- **Longitude**
- **Language**
- **Refresh interval**: 30 minutes, 60 minutes, 3 hours or 6 hours
- **Debug**: normally Off

Default coordinates are Bucharest (`44.4268`, `26.1025`). Replace them with the coordinates of the desired location within the European CAMS pollen coverage area.

## Changing language

Displayed sensor values switch to the selected language on the next successful update.

Domoticz device names are assigned when the devices are first created. If you change language later and also want the **device names** translated, delete the four plugin devices and restart/re-enable the plugin so they are recreated in the new language.

The numeric Alert `nValue` does not change with language, so automations based on `nValue` remain compatible.

## Data source

Pollen forecast data is obtained from the **Open-Meteo Air Quality API** using CAMS European Air Quality forecast data.

Open-Meteo currently provides these pollen variables in Europe: alder, birch, grass, mugwort, olive and ragweed.

Attribution: **Open-Meteo** and **CAMS ENSEMBLE data provider**.

## API and dependencies

The plugin uses only Python standard-library modules.

It does not require:

- API key
- `pip install`
- `requirements.txt`
- virtual environment
- `install.sh`

An internet connection is required only when the plugin refreshes the forecast.

## API errors

If the API or internet connection is temporarily unavailable, the plugin keeps the last successfully received values instead of replacing them with incorrect zero values.

Errors are written to the Domoticz log.

## Requirements

- Domoticz
- Python 3
- Internet connection
- Access to the Open-Meteo API

## Version

**1.1.0**

## Copyright

Copyright © 2026 blooesky. All rights reserved.

The source code is publicly available, but no open-source license is granted for this repository.
