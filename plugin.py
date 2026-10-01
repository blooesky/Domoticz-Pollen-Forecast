# -*- coding: utf-8 -*-
# Pollen Forecast plugin for Domoticz
# Data source: Open-Meteo Air Quality API / CAMS European Air Quality Forecast
# No API key and no external Python packages required.
# Copyright (c) 2026 blooesky. All rights reserved.

"""
<plugin key="PollenForecast" name="Pollen Forecast" author="blooesky" version="1.2.4" externallink="https://github.com/blooesky/Domoticz-Pollen-Forecast">
    <description>
        <h2>Pollen Forecast</h2>
        <p>Creates 4 devices: pollen alert today, pollen alert tomorrow, pollen details today and pollen details tomorrow.</p>
        <p>Supports 14 languages: English, Romanian, German, French, Italian, Spanish, Portuguese, Dutch, Polish, Luxembourgish, Czech, Bulgarian, Hungarian and Swedish.</p>
        <p>Data source: Open-Meteo Air Quality API, based on CAMS European Air Quality Forecast.</p>
    </description>
    <params>
        <param field="Mode1" label="Latitude (optional override)" width="180px" required="false" default=""/>
        <param field="Mode2" label="Longitude (optional override)" width="180px" required="false" default=""/>
        <param field="Mode3" label="Language" width="180px" required="true" default="ro">
            <options>
                <option label="Română" value="ro" default="true"/>
                <option label="English" value="en"/>
                <option label="Deutsch" value="de"/>
                <option label="Français" value="fr"/>
                <option label="Italiano" value="it"/>
                <option label="Español" value="es"/>
                <option label="Português" value="pt"/>
                <option label="Nederlands" value="nl"/>
                <option label="Polski" value="pl"/>
                <option label="Lëtzebuergesch" value="lb"/>
                <option label="Čeština" value="cs"/>
                <option label="Български" value="bg"/>
                <option label="Magyar" value="hu"/>
                <option label="Svenska" value="sv"/>
            </options>
        </param>
        <param field="Mode4" label="Refresh interval" width="180px" required="true" default="60">
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
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request


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
    "de": {
        "device_alert_today": "Pollenwarnung heute",
        "device_alert_tomorrow": "Pollenwarnung morgen",
        "device_today": "Pollen heute",
        "device_tomorrow": "Pollen morgen",
        "levels": {0: "Keine Daten", 1: "Kein", 2: "Niedrig", 3: "Mittel", 4: "Hoch"},
        "pollen": {
            "alder_pollen": "Erle",
            "birch_pollen": "Birke",
            "grass_pollen": "Gräser",
            "mugwort_pollen": "Beifuß",
            "olive_pollen": "Olive",
            "ragweed_pollen": "Ambrosia",
        },
        "no_data": "k. A.",
    },
    "fr": {
        "device_alert_today": "Alerte pollen aujourd'hui",
        "device_alert_tomorrow": "Alerte pollen demain",
        "device_today": "Pollen aujourd'hui",
        "device_tomorrow": "Pollen demain",
        "levels": {0: "Pas de données", 1: "Aucun", 2: "Faible", 3: "Modéré", 4: "Élevé"},
        "pollen": {
            "alder_pollen": "Aulne",
            "birch_pollen": "Bouleau",
            "grass_pollen": "Graminées",
            "mugwort_pollen": "Armoise",
            "olive_pollen": "Olivier",
            "ragweed_pollen": "Ambroisie",
        },
        "no_data": "N/D",
    },
    "it": {
        "device_alert_today": "Allerta polline oggi",
        "device_alert_tomorrow": "Allerta polline domani",
        "device_today": "Polline oggi",
        "device_tomorrow": "Polline domani",
        "levels": {0: "Nessun dato", 1: "Assente", 2: "Basso", 3: "Medio", 4: "Alto"},
        "pollen": {
            "alder_pollen": "Ontano",
            "birch_pollen": "Betulla",
            "grass_pollen": "Graminacee",
            "mugwort_pollen": "Artemisia",
            "olive_pollen": "Olivo",
            "ragweed_pollen": "Ambrosia",
        },
        "no_data": "N/D",
    },
    "es": {
        "device_alert_today": "Alerta de polen hoy",
        "device_alert_tomorrow": "Alerta de polen mañana",
        "device_today": "Polen hoy",
        "device_tomorrow": "Polen mañana",
        "levels": {0: "Sin datos", 1: "Ninguno", 2: "Bajo", 3: "Medio", 4: "Alto"},
        "pollen": {
            "alder_pollen": "Aliso",
            "birch_pollen": "Abedul",
            "grass_pollen": "Gramíneas",
            "mugwort_pollen": "Artemisa",
            "olive_pollen": "Olivo",
            "ragweed_pollen": "Ambrosía",
        },
        "no_data": "N/D",
    },
    "pt": {
        "device_alert_today": "Alerta de pólen hoje",
        "device_alert_tomorrow": "Alerta de pólen amanhã",
        "device_today": "Pólen hoje",
        "device_tomorrow": "Pólen amanhã",
        "levels": {0: "Sem dados", 1: "Nenhum", 2: "Baixo", 3: "Médio", 4: "Alto"},
        "pollen": {
            "alder_pollen": "Amieiro",
            "birch_pollen": "Bétula",
            "grass_pollen": "Gramíneas",
            "mugwort_pollen": "Artemísia",
            "olive_pollen": "Oliveira",
            "ragweed_pollen": "Ambrósia",
        },
        "no_data": "N/D",
    },
    "nl": {
        "device_alert_today": "Pollenwaarschuwing vandaag",
        "device_alert_tomorrow": "Pollenwaarschuwing morgen",
        "device_today": "Pollen vandaag",
        "device_tomorrow": "Pollen morgen",
        "levels": {0: "Geen gegevens", 1: "Geen", 2: "Laag", 3: "Gemiddeld", 4: "Hoog"},
        "pollen": {
            "alder_pollen": "Els",
            "birch_pollen": "Berk",
            "grass_pollen": "Gras",
            "mugwort_pollen": "Bijvoet",
            "olive_pollen": "Olijf",
            "ragweed_pollen": "Ambrosia",
        },
        "no_data": "N/B",
    },
    "pl": {
        "device_alert_today": "Alert pyłkowy dziś",
        "device_alert_tomorrow": "Alert pyłkowy jutro",
        "device_today": "Pyłki dziś",
        "device_tomorrow": "Pyłki jutro",
        "levels": {0: "Brak danych", 1: "Brak", 2: "Niski", 3: "Średni", 4: "Wysoki"},
        "pollen": {
            "alder_pollen": "Olsza",
            "birch_pollen": "Brzoza",
            "grass_pollen": "Trawy",
            "mugwort_pollen": "Bylica",
            "olive_pollen": "Oliwka",
            "ragweed_pollen": "Ambrozja",
        },
        "no_data": "B/D",
    },
    "lb": {
        "device_alert_today": "Pollenalarm haut",
        "device_alert_tomorrow": "Pollenalarm muer",
        "device_today": "Pollen haut",
        "device_tomorrow": "Pollen muer",
        "levels": {0: "Keng Donnéeën", 1: "Keng", 2: "Niddereg", 3: "Mëttel", 4: "Héich"},
        "pollen": {
            "alder_pollen": "Erle",
            "birch_pollen": "Birk",
            "grass_pollen": "Gras",
            "mugwort_pollen": "Beifouss",
            "olive_pollen": "Oliven",
            "ragweed_pollen": "Ambrosia",
        },
        "no_data": "Keng Donnéeën",
    },
    "cs": {
        "device_alert_today": "Pylové varování dnes",
        "device_alert_tomorrow": "Pylové varování zítra",
        "device_today": "Pyl dnes",
        "device_tomorrow": "Pyl zítra",
        "levels": {0: "Bez dat", 1: "Žádný", 2: "Nízký", 3: "Střední", 4: "Vysoký"},
        "pollen": {
            "alder_pollen": "Olše",
            "birch_pollen": "Bříza",
            "grass_pollen": "Trávy",
            "mugwort_pollen": "Pelyněk",
            "olive_pollen": "Olivovník",
            "ragweed_pollen": "Ambrozie",
        },
        "no_data": "N/A",
    },
    "bg": {
        "device_alert_today": "Предупреждение за полени днес",
        "device_alert_tomorrow": "Предупреждение за полени утре",
        "device_today": "Полени днес",
        "device_tomorrow": "Полени утре",
        "levels": {0: "Без данни", 1: "Няма", 2: "Ниско", 3: "Средно", 4: "Високо"},
        "pollen": {
            "alder_pollen": "Елша",
            "birch_pollen": "Бреза",
            "grass_pollen": "Треви",
            "mugwort_pollen": "Пелин",
            "olive_pollen": "Маслина",
            "ragweed_pollen": "Амброзия",
        },
        "no_data": "Н/Д",
    },
    "hu": {
        "device_alert_today": "Pollenriasztás ma",
        "device_alert_tomorrow": "Pollenriasztás holnap",
        "device_today": "Pollen ma",
        "device_tomorrow": "Pollen holnap",
        "levels": {0: "Nincs adat", 1: "Nincs", 2: "Alacsony", 3: "Közepes", 4: "Magas"},
        "pollen": {
            "alder_pollen": "Éger",
            "birch_pollen": "Nyír",
            "grass_pollen": "Fűfélék",
            "mugwort_pollen": "Üröm",
            "olive_pollen": "Olajfa",
            "ragweed_pollen": "Parlagfű",
        },
        "no_data": "N/A",
    },
    "sv": {
        "device_alert_today": "Pollenvarning idag",
        "device_alert_tomorrow": "Pollenvarning imorgon",
        "device_today": "Pollen idag",
        "device_tomorrow": "Pollen imorgon",
        "levels": {0: "Inga data", 1: "Ingen", 2: "Låg", 3: "Medel", 4: "Hög"},
        "pollen": {
            "alder_pollen": "Al",
            "birch_pollen": "Björk",
            "grass_pollen": "Gräs",
            "mugwort_pollen": "Gråbo",
            "olive_pollen": "Oliv",
            "ragweed_pollen": "Ambrosia",
        },
        "no_data": "N/A",
    },
}


class BasePlugin:
    def __init__(self):
        self.latitude = None
        self.longitude = None
        self.language = "ro"
        self.refresh_minutes = 60
        self.last_update = 0
        self.debug = False
        self.use_domoticz_location = True
        self.location_source = None
        self.next_location_retry_at = 0
        self.location_retry_seconds = 60
        self._location_error_reported = False

    def onStart(self):
        self._load_config()
        self._create_devices()
        Domoticz.Heartbeat(30)
        self._log("Plugin started")
        self._update_pollen()

    def onStop(self):
        self._log("Plugin stopped")

    def onHeartbeat(self):
        now = time.time()

        # If Domoticz location was not ready at startup, retry quickly instead
        # of waiting for the normal pollen refresh interval. A cached location
        # can still be used for forecasts while these recovery attempts run.
        if self.use_domoticz_location:
            if self.latitude is None or self.longitude is None:
                if now >= self.next_location_retry_at:
                    self._update_pollen()
                return

            if self.location_source == "cache" and now >= self.next_location_retry_at:
                previous = (self.latitude, self.longitude)
                self._load_domoticz_location()
                if self.location_source != "cache" and (self.latitude, self.longitude) != previous:
                    self.last_update = 0

        if now - self.last_update >= self.refresh_minutes * 60:
            self._update_pollen()

    def _load_config(self):
        latitude_text = Parameters.get("Mode1", "").strip()
        longitude_text = Parameters.get("Mode2", "").strip()

        # Empty override fields mean: use the global Domoticz location from
        # Setup -> Settings -> Location. If both fields are filled in, they
        # override the Domoticz location for this plugin instance only.
        if latitude_text == "" and longitude_text == "":
            self.use_domoticz_location = True
            self.latitude = None
            self.longitude = None
        elif latitude_text != "" and longitude_text != "":
            self.use_domoticz_location = False
            try:
                latitude = float(latitude_text)
                longitude = float(longitude_text)
                self._validate_coordinates(latitude, longitude)
                self.latitude = latitude
                self.longitude = longitude
            except (TypeError, ValueError) as exc:
                self.latitude = None
                self.longitude = None
                Domoticz.Error("Invalid custom Latitude/Longitude: {}".format(exc))
        else:
            self.use_domoticz_location = False
            self.latitude = None
            self.longitude = None
            Domoticz.Error("Custom location requires both Latitude and Longitude, or leave both fields empty to use the Domoticz location.")

        lang = Parameters.get("Mode3", "ro").strip().lower()
        self.language = lang if lang in TEXT else "ro"

        try:
            self.refresh_minutes = max(30, int(Parameters.get("Mode4", "60")))
        except (TypeError, ValueError):
            self.refresh_minutes = 60

        self.debug = Parameters.get("Mode5", "0") == "1"


    def _read_persistent_config(self):
        try:
            config = Domoticz.Configuration()
            return config if isinstance(config, dict) else {}
        except Exception as exc:
            self._log("Domoticz.Configuration read failed: {}".format(exc))
            return {}

    def _save_cached_location(self, latitude, longitude):
        """Persist the last valid Domoticz location in the Domoticz database."""
        try:
            config = self._read_persistent_config()
            lat_text = "{:.8f}".format(float(latitude))
            lon_text = "{:.8f}".format(float(longitude))

            if (
                config.get("last_known_latitude") == lat_text
                and config.get("last_known_longitude") == lon_text
            ):
                return

            config["last_known_latitude"] = lat_text
            config["last_known_longitude"] = lon_text
            config["last_known_location_saved_at"] = str(int(time.time()))
            Domoticz.Configuration(config)
            self._log("Saved last known Domoticz location")
        except Exception as exc:
            self._log("Domoticz.Configuration write failed: {}".format(exc))

    def _load_cached_location(self):
        """Return the last valid Domoticz location stored by this plugin."""
        config = self._read_persistent_config()
        latitude = config.get("last_known_latitude")
        longitude = config.get("last_known_longitude")

        if latitude in (None, "") or longitude in (None, ""):
            return None

        try:
            latitude = float(latitude)
            longitude = float(longitude)
            self._validate_coordinates(latitude, longitude)
            return latitude, longitude
        except (TypeError, ValueError):
            self._log("Ignoring invalid cached Domoticz location")
            return None

    @staticmethod
    def _validate_coordinates(latitude, longitude):
        if not -90.0 <= latitude <= 90.0:
            raise ValueError("Latitude out of range")
        if not -180.0 <= longitude <= 180.0:
            raise ValueError("Longitude out of range")

    @staticmethod
    def _parse_location_value(value):
        """Return (lat, lon) when value contains a usable Domoticz location."""
        if isinstance(value, dict):
            latitude = value.get("Latitude", value.get("latitude"))
            longitude = value.get("Longitude", value.get("longitude"))
            if latitude not in (None, "") and longitude not in (None, ""):
                return latitude, longitude
            return None

        # Some versions/plugins expose compound values as text. Accept the
        # common "lat;lon" and "lat,lon" representations as a compatibility
        # fallback.
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            match = re.match(
                r"^\s*([-+]?\d+(?:\.\d+)?)\s*[,;]\s*([-+]?\d+(?:\.\d+)?)\s*$",
                text,
            )
            if match:
                return match.group(1), match.group(2)

        return None

    @staticmethod
    def _extract_location(container):
        """Extract latitude/longitude from known Domoticz settings layouts."""
        if not isinstance(container, dict):
            return None

        # JSON getsettings uses: Location: {Latitude: ..., Longitude: ...}
        for key in ("Location", "location"):
            if key in container:
                parsed = BasePlugin._parse_location_value(container.get(key))
                if parsed:
                    return parsed

        # Compatibility with flat preference dictionaries.
        latitude = None
        longitude = None
        latitude_keys = (
            "Latitude", "latitude", "LocationLatitude", "locationLatitude",
            "Location_Latitude", "LocationLat", "lat",
        )
        longitude_keys = (
            "Longitude", "longitude", "LocationLongitude", "locationLongitude",
            "Location_Longitude", "LocationLon", "LocationLng", "lon", "lng",
        )

        for key in latitude_keys:
            if key in container and container.get(key) not in (None, ""):
                latitude = container.get(key)
                break
        for key in longitude_keys:
            if key in container and container.get(key) not in (None, ""):
                longitude = container.get(key)
                break

        if latitude not in (None, "") and longitude not in (None, ""):
            return latitude, longitude

        return None

    def _local_domoticz_urls(self):
        """Build local Domoticz API candidates without requiring user config."""
        http_ports = []
        https_ports = []

        # On Linux the plugin runs inside the Domoticz process. Reading the
        # process command line lets us honor custom -www / -sslwww ports.
        cmdline = []
        try:
            if os.path.exists("/proc/self/cmdline"):
                raw = open("/proc/self/cmdline", "rb").read()
                cmdline = [part.decode("utf-8", "ignore") for part in raw.split(b"\0") if part]
        except Exception:
            cmdline = []

        if not cmdline:
            try:
                cmdline = list(sys.argv)
            except Exception:
                cmdline = []

        for index, item in enumerate(cmdline):
            if item == "-www" and index + 1 < len(cmdline):
                try:
                    port = int(cmdline[index + 1])
                    if port > 0:
                        http_ports.append(port)
                except (TypeError, ValueError):
                    pass
            elif item.startswith("-www="):
                try:
                    port = int(item.split("=", 1)[1])
                    if port > 0:
                        http_ports.append(port)
                except (TypeError, ValueError):
                    pass
            elif item == "-sslwww" and index + 1 < len(cmdline):
                try:
                    port = int(cmdline[index + 1])
                    if port > 0:
                        https_ports.append(port)
                except (TypeError, ValueError):
                    pass
            elif item.startswith("-sslwww="):
                try:
                    port = int(item.split("=", 1)[1])
                    if port > 0:
                        https_ports.append(port)
                except (TypeError, ValueError):
                    pass

        # Standard Domoticz ports remain useful on Windows and installations
        # where command-line arguments are not visible to the embedded Python.
        if 8080 not in http_ports:
            http_ports.append(8080)
        if 443 not in https_ports:
            https_ports.append(443)

        urls = []
        for port in http_ports:
            urls.append("http://127.0.0.1:{}/json.htm?type=command&param=getsettings".format(port))
        for port in https_ports:
            urls.append("https://127.0.0.1:{}/json.htm?type=command&param=getsettings".format(port))
        return urls

    def _load_location_from_local_api(self):
        """Read Setup -> Settings -> Location through the local Domoticz API."""
        ssl_context = ssl._create_unverified_context()

        for url in self._local_domoticz_urls():
            try:
                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Domoticz-PollenForecast/1.2.4",
                        "Accept": "application/json",
                    },
                )
                kwargs = {"timeout": 3}
                if url.startswith("https://"):
                    kwargs["context"] = ssl_context

                with urllib.request.urlopen(request, **kwargs) as response:
                    if response.status != 200:
                        continue
                    payload = json.loads(response.read().decode("utf-8"))

                parsed = self._extract_location(payload)
                if parsed:
                    self._log("Domoticz location read from local API via {}".format(url.split("/json.htm", 1)[0]))
                    return parsed
            except Exception as exc:
                self._log("Local Domoticz location lookup failed via {}: {}".format(url, exc))

        return None

    def _load_domoticz_location(self):
        """Load Domoticz location, falling back to the last known valid value."""
        parsed = None
        source = None

        # First use the Python plugin Settings dictionary when the running
        # Domoticz version exposes location data there.
        try:
            settings = globals().get("Settings", {})
            parsed = self._extract_location(settings)
            if parsed:
                source = "settings"
        except Exception as exc:
            self._log("Unable to inspect Python Settings for location: {}".format(exc))

        # The local getsettings response reliably exposes a nested Location
        # object, while the Python Settings dictionary can differ by version.
        if not parsed:
            parsed = self._load_location_from_local_api()
            if parsed:
                source = "api"

        if parsed:
            try:
                latitude = float(parsed[0])
                longitude = float(parsed[1])
                self._validate_coordinates(latitude, longitude)
                self.latitude = latitude
                self.longitude = longitude
                self.location_source = source
                self.next_location_retry_at = 0
                self._location_error_reported = False
                self._save_cached_location(latitude, longitude)
                self._log("Using Domoticz location from {}: {}, {}".format(source, latitude, longitude))
                return True
            except (TypeError, ValueError) as exc:
                self._log("Invalid Domoticz location returned by {}: {}".format(source, exc))

        # Domoticz can temporarily be unavailable during startup. Use the last
        # valid automatic location saved in Domoticz.Configuration so pollen
        # updates can continue while we retry the live location in the background.
        cached = self._load_cached_location()
        if cached:
            self.latitude, self.longitude = cached
            self.location_source = "cache"
            self.next_location_retry_at = time.time() + self.location_retry_seconds
            self._location_error_reported = False
            self._log(
                "Live Domoticz location unavailable; using last known location: {}, {}".format(
                    self.latitude, self.longitude
                )
            )
            return True

        self.latitude = None
        self.longitude = None
        self.location_source = None
        self.next_location_retry_at = time.time() + self.location_retry_seconds

        if not self._location_error_reported:
            Domoticz.Error(
                "Unable to read a valid location from Domoticz and no last known location is cached. "
                "The plugin will retry automatically; alternatively enter custom Latitude/Longitude in Hardware settings."
            )
            self._location_error_reported = True
        return False

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

        # When no custom coordinates are configured, follow the current
        # location from Domoticz Settings on every refresh.
        if self.use_domoticz_location:
            self._load_domoticz_location()

        if self.latitude is None or self.longitude is None:
            # In automatic-location mode _load_domoticz_location() already
            # scheduled a short retry and logged the problem once. Do not move
            # last_update forward, otherwise the retry would wait for the full
            # pollen refresh interval.
            if not self.use_domoticz_location:
                Domoticz.Error(
                    "Pollen update skipped: enter both custom Latitude and Longitude values, or leave both empty to use the Domoticz location."
                )
                self.last_update = time.time()
            return

        try:
            data = self._fetch_api()
            days = self._build_daily_data(data)

            if len(days) < 2:
                raise ValueError("API response does not contain both today and tomorrow")

            self._update_day(alert_unit=1, text_unit=3, day=days[0])
            self._update_day(alert_unit=2, text_unit=4, day=days[1])

            self.last_update = time.time()
            self._log("Pollen forecast updated successfully")

        except Exception as exc:
            Domoticz.Error("Pollen update failed: {}".format(exc))
            # Keep the previous valid values in Domoticz and retry at the next interval.
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
                "User-Agent": "Domoticz-PollenForecast/1.2.4",
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

        # Alert sValue contains ONLY the overall level. This is intentional so
        # notifications and automations remain simple and reliable.
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
