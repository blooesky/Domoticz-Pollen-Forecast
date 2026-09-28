# -*- coding: utf-8 -*-
# Pollen Forecast plugin for Domoticz
# Data source: Open-Meteo Air Quality API / CAMS European Air Quality Forecast
# No API key and no external Python packages required.

"""
<plugin key="PollenForecast" name="Pollen Forecast" author="4D" version="1.0.1" externallink="https://open-meteo.com/en/docs/air-quality-api">
    <description>
        <h2>Pollen Forecast / Prognoză polen</h2>
        <p>Creates 4 devices: pollen alert today, pollen alert tomorrow, pollen details today and pollen details tomorrow.</p>
        <p>Creeaza 4 dispozitive: alertă polen azi, alertă polen mâine, detalii polen azi si detalii polen mâine.</p>
        <p>Data: Open-Meteo Air Quality API, based on CAMS European Air Quality Forecast.</p>
    </description>
    <params>
        <param field="Mode1" label="Latitude / Latitudine" width="120px" required="true" default=""/>
        <param field="Mode2" label="Longitude / Longitudine" width="120px" required="true" default=""/>
        <param field="Mode3" label="Language / Limbă" width="160px" required="true" default="ro">
            <options>
                <option label="English" value="en" default="true"/>
                <option label="Română" value="ro" />
            </options>
        </param>
        <param field="Mode4" label="Refresh interval / Interval actualizare" width="180px" required="true" default="60">
            <options>
                <option label="30 minutes" value="30"/>
                <option label="60 minutes" value="60" default="true"/>
                <option label="3 hours" value="180"/>
                <option label="6 hours" value="360"/>
            </options>
        </param>
        <param field="Mode5" label="Debug" width="100px" required="true" default="0">
            <options>
                <option label="Off" value="0" default="true"/>
                <option label="On" value="1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime


API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

POLLEN_TYPES = (
    "alder_pollen",
    "birch_pollen",
    "grass_pollen",
    "mugwort_pollen",
    "olive_pollen",
    "ragweed_pollen",
)

# Four concentration classes: None, Low, Medium, High.
# Thresholds are mapped from aerobiological pollen-family concentration bands:
# Betulaceae: 0-0.9 / 1-16 / 16.1-50 / >50
# Graminaceae: 0-0.9 / 1-10 / 10.1-30 / >30
# Oleaceae:    0-0.9 / 1-5  / 5.1-25  / >25
# Compositae:  0-0.9 / 1-5  / 5.1-25  / >25
# Tuple values below are the upper limits for Low and Medium.
THRESHOLDS = {
    "alder_pollen": (16.0, 50.0),
    "birch_pollen": (16.0, 50.0),
    "grass_pollen": (10.0, 30.0),
    "mugwort_pollen": (5.0, 25.0),
    "olive_pollen": (5.0, 25.0),
    "ragweed_pollen": (5.0, 25.0),
}

TEXT = {
    "en": {
        "device_alert_today": "Pollen Alert Today",
        "device_alert_tomorrow": "Pollen Alert Tomorrow",
        "device_today": "Pollen Today",
        "device_tomorrow": "Pollen Tomorrow",
        "levels": {0: "No data", 1: "None", 2: "Low", 3: "Medium", 4: "High"},
        "pollen": {
            "alder_pollen": "Alder",
            "birch_pollen": "Birch",
            "grass_pollen": "Grass",
            "mugwort_pollen": "Mugwort",
            "olive_pollen": "Olive",
            "ragweed_pollen": "Ragweed",
        },
        "no_data": "N/A",
    },
    "ro": {
        "device_alert_today": "Alertă polen azi",
        "device_alert_tomorrow": "Alertă polen mâine",
        "device_today": "Polen azi",
        "device_tomorrow": "Polen mâine",
        "levels": {0: "Fără date", 1: "Fără", 2: "Mic", 3: "Mediu", 4: "Mare"},
        "pollen": {
            "alder_pollen": "Arin",
            "birch_pollen": "Mesteacăn",
            "grass_pollen": "Iarbă",
            "mugwort_pollen": "Pelin",
            "olive_pollen": "Măslin",
            "ragweed_pollen": "Ambrozie",
        },
        "no_data": "N/D",
    },
}


class BasePlugin:
    def __init__(self):
        self.latitude = 44.4268
        self.longitude = 26.1025
        self.language = "ro"
        self.refresh_minutes = 60
        self.last_update = 0
        self.debug = False

    def onStart(self):
        self._load_config()
        self._create_devices()
        Domoticz.Heartbeat(30)
        self._log("Plugin started")
        self._update_pollen()

    def onStop(self):
        self._log("Plugin stopped")

    def onHeartbeat(self):
        if time.time() - self.last_update >= self.refresh_minutes * 60:
            self._update_pollen()

    def _load_config(self):
        try:
            self.latitude = float(Parameters.get("Mode1", "44.4268").strip())
            self.longitude = float(Parameters.get("Mode2", "26.1025").strip())
        except (TypeError, ValueError):
            Domoticz.Error("Invalid latitude or longitude. Using Bucharest defaults.")
            self.latitude = 44.4268
            self.longitude = 26.1025

        lang = Parameters.get("Mode3", "ro").strip().lower()
        self.language = lang if lang in TEXT else "ro"

        try:
            self.refresh_minutes = max(30, int(Parameters.get("Mode4", "60")))
        except (TypeError, ValueError):
            self.refresh_minutes = 60

        self.debug = Parameters.get("Mode5", "0") == "1"

    def _create_devices(self):
        t = TEXT[self.language]

        # Domoticz Alert device levels:
        # 0 = grey/no data, 1 = green, 2 = yellow, 3 = orange, 4 = red.
        if 1 not in Devices:
            Domoticz.Device(Name=t["device_alert_today"], Unit=1, TypeName="Alert", Used=1).Create()
        if 2 not in Devices:
            Domoticz.Device(Name=t["device_alert_tomorrow"], Unit=2, TypeName="Alert", Used=1).Create()
        if 3 not in Devices:
            Domoticz.Device(Name=t["device_today"], Unit=3, TypeName="Text", Used=1).Create()
        if 4 not in Devices:
            Domoticz.Device(Name=t["device_tomorrow"], Unit=4, TypeName="Text", Used=1).Create()

    def _update_pollen(self):
        self._log("Updating pollen forecast...")

        try:
            data = self._fetch_api()
            days = self._build_daily_data(data)

            if len(days) < 2:
                raise ValueError("API response does not contain both today and tomorrow")

            today = days[0]
            tomorrow = days[1]

            self._update_day(alert_unit=1, text_unit=3, day=today)
            self._update_day(alert_unit=2, text_unit=4, day=tomorrow)

            self.last_update = time.time()
            self._log("Pollen forecast updated successfully")

        except Exception as exc:
            Domoticz.Error("Pollen update failed: {}".format(exc))
            # Keep the previous valid values in Domoticz and retry on the next heartbeat.
            # Avoid a tight retry loop after an API/network failure.
            self.last_update = time.time()

    def _fetch_api(self):
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": ",".join(POLLEN_TYPES),
            "timezone": "auto",
            "forecast_days": 2,
            "domains": "cams_europe",
        }
        url = API_URL + "?" + urllib.parse.urlencode(params)
        self._log("API URL: {}".format(url))

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Domoticz-PollenForecast/1.0",
                "Accept": "application/json",
            },
        )

        with urllib.request.urlopen(request, timeout=8) as response:
            if response.status != 200:
                raise RuntimeError("HTTP {}".format(response.status))
            payload = response.read().decode("utf-8")

        data = json.loads(payload)
        if data.get("error"):
            raise RuntimeError(data.get("reason", "Open-Meteo API error"))
        if "hourly" not in data or "time" not in data["hourly"]:
            raise ValueError("Invalid Open-Meteo response")
        return data

    def _build_daily_data(self, data):
        hourly = data["hourly"]
        times = hourly.get("time", [])
        if not times:
            return []

        # forecast_days=2 and timezone=auto make the API start at local 00:00.
        # We still group by the actual date returned by the API for robustness.
        dates = []
        for ts in times:
            day = ts[:10]
            if day not in dates:
                dates.append(day)

        result = []
        for day in dates[:2]:
            item = {"date": day, "values": {}}
            indices = [i for i, ts in enumerate(times) if ts.startswith(day)]

            for pollen in POLLEN_TYPES:
                series = hourly.get(pollen, [])
                values = []
                for i in indices:
                    if i >= len(series):
                        continue
                    value = series[i]
                    if value is None:
                        continue
                    try:
                        values.append(float(value))
                    except (TypeError, ValueError):
                        continue

                # Use the highest hourly concentration forecast for the day.
                item["values"][pollen] = max(values) if values else None

            result.append(item)

        return result

    def _level_for(self, pollen, concentration):
        if concentration is None:
            return 0
        if concentration < 1.0:
            return 1

        low_max, medium_max = THRESHOLDS[pollen]
        if concentration <= low_max:
            return 2
        if concentration <= medium_max:
            return 3
        return 4

    def _update_day(self, alert_unit, text_unit, day):
        t = TEXT[self.language]
        levels = {}

        for pollen in POLLEN_TYPES:
            levels[pollen] = self._level_for(pollen, day["values"].get(pollen))

        available_levels = [level for level in levels.values() if level > 0]
        overall = max(available_levels) if available_levels else 0

        # Keep Alert sValue intentionally simple so Domoticz automations can
        # match it reliably: None/Low/Medium/High or Fără/Mic/Mediu/Mare.
        # Pollen types remain available only in the Text devices.
        alert_text = t["levels"][overall]

        details = []
        for pollen in POLLEN_TYPES:
            concentration = day["values"].get(pollen)
            level = levels[pollen]
            if concentration is None:
                level_text = t["no_data"]
            else:
                level_text = t["levels"][level]
            details.append("{}: {}".format(t["pollen"][pollen], level_text))

        details_text = " | ".join(details)

        self._device_update(alert_unit, overall, alert_text)
        self._device_update(text_unit, 0, details_text)

        self._log("{} -> {} | {}".format(day["date"], alert_text, details_text))

    @staticmethod
    def _device_update(unit, nvalue, svalue):
        if unit not in Devices:
            return
        device = Devices[unit]
        if device.nValue != nvalue or device.sValue != svalue:
            device.Update(nValue=nvalue, sValue=svalue)

    def _log(self, message):
        if self.debug:
            Domoticz.Log(message)


_global_plugin = BasePlugin()


def onStart():
    _global_plugin.onStart()


def onStop():
    _global_plugin.onStop()


def onHeartbeat():
    _global_plugin.onHeartbeat()
