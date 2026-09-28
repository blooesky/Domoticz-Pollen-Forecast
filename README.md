# Domoticz Pollen Forecast Plugin  for EU

A simple bilingual Domoticz plugin for monitoring airborne pollen levels using the free **Open-Meteo Air Quality API**.
Pollen data is currently available only in Europe.
The plugin provides pollen alerts for **today** and **tomorrow**, together with detailed pollen information for each supported pollen type.

No API key and no external Python libraries are required.

Repository:

```text
https://github.com/blooesky/Domoticz-Pollen-Forecast
```

## Features

- Free Open-Meteo Air Quality API
- No API key required
- No external Python dependencies
- No installer required
- English and Romanian interface
- Configurable latitude and longitude
- Configurable update interval
- Separate pollen forecast for today and tomorrow
- Domoticz Alert sensors suitable for automations and notifications
- Detailed pollen information using Text sensors
- Keeps the last valid values if the API is temporarily unavailable

## Supported pollen types

The plugin monitors:

- Alder
- Birch
- Grass
- Mugwort
- Olive
- Ragweed

Romanian names:

- Arin
- Mesteacăn
- Iarbă
- Pelin
- Măslin
- Ambrozie

## Devices

The plugin automatically creates four Domoticz devices.

### Pollen Alert Today

Shows only the overall pollen level for today.

English:

- None
- Low
- Medium
- High

Romanian:

- Fără
- Mic
- Mediu
- Mare

The sensor does not display the pollen type, making it suitable for Domoticz automations and notifications.

The alert level is determined by the highest pollen level detected among all supported pollen types.

### Pollen Alert Tomorrow

Shows only the overall pollen level forecast for tomorrow.

English:

- None
- Low
- Medium
- High

Romanian:

- Fără
- Mic
- Mediu
- Mare

As with today's alert, no pollen type is displayed in this sensor.

### Pollen Today

Text sensor containing detailed pollen information for today.

Example:

```text
Alder: None | Birch: Low | Grass: Medium | Mugwort: None | Olive: None | Ragweed: High
```

Romanian example:

```text
Arin: Fără | Mesteacăn: Mic | Iarbă: Mediu | Pelin: Fără | Măslin: Fără | Ambrozie: Mare
```

### Pollen Tomorrow

Text sensor containing detailed pollen information for tomorrow.

Example:

```text
Alder: Low | Birch: Low | Grass: High | Mugwort: None | Olive: None | Ragweed: Medium
```

## Alert values

The Domoticz Alert devices use the following `nValue` values:

| nValue | English | Romanian |
|---:|---|---|
| 0 | No data | Fără date |
| 1 | None | Fără |
| 2 | Low | Mic |
| 3 | Medium | Mediu |
| 4 | High | Mare |

This makes the Alert sensors easy to use in Domoticz automations.

For example:

```text
nValue >= 3
```

means that the pollen level is:

```text
Medium or High
```

or:

```text
Mediu sau Mare
```

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

Then open:

**Setup → Hardware**

and add:

**Pollen Forecast**

## Manual installation

You can also download the repository manually and copy it to:

```text
/home/pi/domoticz/plugins/PollenForecast/
```

The folder should contain:

```text
PollenForecast/
├── plugin.py
└── README.md
```

Restart Domoticz after copying the files:

```bash
sudo systemctl restart domoticz
```

## Update

If the plugin was installed using Git, updating it is very simple.

Go to the plugin directory:

```bash
cd /home/pi/domoticz/plugins/PollenForecast
```

Download the latest version:

```bash
git pull
```

Restart Domoticz:

```bash
sudo systemctl restart domoticz
```

Complete update command:

```bash
cd /home/pi/domoticz/plugins/PollenForecast
git pull
sudo systemctl restart domoticz
```

Existing devices and plugin settings are preserved during normal updates.

## Configuration

After adding the plugin from **Setup → Hardware**, the following options are available.

### Latitude

Latitude of the location for which pollen data should be retrieved.

Example:

```text
44.4268
```

### Longitude

Longitude of the location.

Example:

```text
26.1025
```

### Language

Available languages:

- English
- Română

Device names, pollen types and pollen levels are automatically translated according to the selected language.

### Update interval

Available update intervals:

- 30 minutes
- 60 minutes
- 3 hours
- 6 hours

Pollen forecast data normally changes relatively slowly, so an update every 1–3 hours is usually sufficient.

### Debug

Debug logging can be enabled from the plugin configuration if troubleshooting is required.

For normal operation, Debug should remain disabled.

## Dependencies

The plugin uses only standard Python libraries.

No additional Python packages are required.

## Data source

Pollen data is retrieved from the **Open-Meteo Air Quality API**.

The API provides pollen concentration data for Europe for several pollen types.

Pollen concentration values are expressed in:

```text
grains/m³
```

The plugin retrieves hourly forecast data and determines the maximum concentration for each pollen type during the day.

The concentration is then converted into one of four simple levels:

```text
None
Low
Medium
High
```

or in Romanian:

```text
Fără
Mic
Mediu
Mare
```

The overall Alert sensor uses the highest pollen level detected during that day.

## Why use the daily maximum?

Pollen concentrations can vary considerably during the day.

Using the highest forecast concentration rather than the daily average helps ensure that short periods of elevated pollen concentration are not hidden by lower values from the rest of the day.

This also makes the Alert sensors more useful for notifications and automations.

## Domoticz automation

Because the two Alert sensors use standard Domoticz Alert levels, they can easily be used in dzVents, Blockly or other Domoticz automation systems.

Example condition:

```text
Alert level >= 3
```

This triggers when the pollen level is:

```text
Medium
```

or:

```text
High
```

## dzVents example

Example notification when today's pollen level becomes Medium or High:

```lua
return {
    on = {
        devices = {
            'Pollen Alert Today'
        }
    },

    execute = function(domoticz, device)

        if device.level >= 3 then

            domoticz.notify(
                'Pollen Alert',
                'Pollen level today is ' .. device.text,
                domoticz.PRIORITY_NORMAL
            )

        end

    end
}
```

For Romanian language configuration, use the Romanian device name:

```text
Alertă polen azi
```

Example:

```lua
return {
    on = {
        devices = {
            'Alertă polen azi'
        }
    },

    execute = function(domoticz, device)

        if device.level >= 3 then

            domoticz.notify(
                'Alertă polen',
                'Nivelul de polen pentru astăzi este ' .. device.text,
                domoticz.PRIORITY_NORMAL
            )

        end

    end
}
```

## API errors

If the Open-Meteo API is temporarily unavailable or the internet connection is interrupted, the plugin does not overwrite the existing sensors with incorrect values.

The last successfully received values remain available in Domoticz until new valid data can be retrieved.

Errors are reported in the Domoticz log.

## Internet connection

An internet connection is required when pollen data is updated.

The plugin does not maintain a permanent connection to the API.

It connects only when an update is required.

## API key

No API key is required.

## Requirements

- Domoticz
- Python 3
- Internet connection
- Access to the Open-Meteo API

## Language support

Currently supported languages:

- 🇬🇧 English
- 🇷🇴 Romanian

## Repository

GitHub:

```text
https://github.com/blooesky/Domoticz-Pollen-Forecast
```

Clone:

```bash
git clone https://github.com/blooesky/Domoticz-Pollen-Forecast.git PollenForecast
```

Update:

```bash
cd /home/pi/domoticz/plugins/PollenForecast
git pull
sudo systemctl restart domoticz
```

## Version

Current version:

```text
1.0.1
```

## License

This project can be distributed under the MIT License.
