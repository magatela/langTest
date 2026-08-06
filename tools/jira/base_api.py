# base_api.py
"""
Basis-Client für REST-Aufrufe gegen Jira-basierte APIs.

Alle gemeinsamen Funktionalitäten (Header-Handling, Authentifizierung,
optionale Proxy-Konfiguration, Logging, HTTP-Methoden) werden hier gekapselt,
damit abgeleitete Klassen (z. B. JiraAPI, XrayAPI) sich nur noch um ihre
fachspezifischen Endpunkte kümmern müssen.
"""

from __future__ import annotations
import json
import logging
from typing import Dict, Optional

import requests
from requests import Response, Session
from requests.auth import HTTPBasicAuth


class RestAPIClient:
    """Abstrakte Basisklasse für einfache REST-Clients."""

    #: Standard-Header für alle Anfragen
    DEFAULT_HEADERS: Dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
    }

    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        *,
        proxies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Parameter
        ---------
        base_url:
            Basis-URL der Jira-Instanz, z. B. ``https://jira.example.com/``
            (ohne *rest/api/...*).
        user / password:
            Jira-Benutzerdaten.
        proxies:
            Optionales Proxy-Dictionary wie bei ``requests`` (z. B.
            ``{"http": "http://proxy:8080", "https": "http://proxy:8080"}``).
            Kann später über :meth:`set_proxies` angepasst werden.
        headers:
            Zusätzliche oder zu überschreibende HTTP-Header.
        logger:
            Wenn *None*, wird ein ``logging.getLogger(classname)`` erzeugt.
        session:
            Eigene ``requests.Session`` (für Connection-Pooling, Retry-Strategien
            usw.). Falls *None*, wird intern eine neue Session angelegt.
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.auth = HTTPBasicAuth(user, password)
        self._proxies = proxies  # kann None sein
        self.headers = {**self.DEFAULT_HEADERS, **(headers or {})}
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.session: Session = session or requests.Session()

    # ------------------------------------------------------------------ #
    # Öffentliche Hilfs­funktionen                                       #
    # ------------------------------------------------------------------ #

    def set_proxies(self, proxies: Optional[Dict[str, str]]) -> None:
        """Proxy-Konfiguration nachträglich ändern oder komplett deaktivieren."""
        self.logger.debug("Proxy-Einstellung geändert: %s", proxies)
        self._proxies = proxies

    # ------------------------------------------------------------------ #
    # HTTP-Methoden                                                      #
    # ------------------------------------------------------------------ #

    def get(self, endpoint: str, **kwargs) -> Response:
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, data=None, **kwargs) -> Response:
        if data is not None:
            kwargs['data'] = json.dumps(data, ensure_ascii=False).encode('utf-8')
        return self._request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, data=None, **kwargs) -> Response:
        if data is not None:
            kwargs['data'] = json.dumps(data, ensure_ascii=False).encode('utf-8')
        return self._request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Response:
        return self._request("DELETE", endpoint, **kwargs)

    # ------------------------------------------------------------------ #
    # Interne Implementierung                                            #
    # ------------------------------------------------------------------ #

    def _request(self, method: str, endpoint: str, **kwargs) -> Response:
        """
        Führt einen HTTP-Request aus und gibt das ``Response``-Objekt zurück.
        Ein JSON-Payload wird automatisch serialisiert, Header & Proxys werden
        ergänzt.
        """
        url = endpoint if endpoint.startswith("http") else self.base_url + endpoint
        self.logger.debug("%s %s", method, url)

        # Standard-Header + evtl. übergebene Header
        hdrs = {**self.headers, **kwargs.pop("headers", {})}
        
        resp = self.session.request(
            method,
            url,
            auth=self.auth,
            headers=hdrs,
            proxies=self._proxies,
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )

        # Fehler protokollieren, aber nicht automatisch Exception werfen –
        # das überlassen wir den Aufrufern.
        if not resp.ok:
            try:
                error_payload = resp.json()
            except ValueError:
                error_payload = resp.text
            print(f"Fehlerhafte Antwort {resp.status_code} für {method} {url} {error_payload}")
            self.logger.debug(f"Fehlerhafte Antwort {resp.status_code} für {method} {url} {error_payload}")
        return resp

    # ------------------------------------------------------------------ #
    # Utility: Antwort als JSON-Datei sichern (debugging)                #
    # ------------------------------------------------------------------ #

    def save_response(self, response: Response, path: str = "response.json") -> None:
        """Antwort­inhalt (JSON) in Datei schreiben – für Debugging-Zwecke."""
        try:
            data = response.json()
        except ValueError:
            self.logger.error("Keine gültige JSON-Antwort → %s", path)
            data = {"raw": response.text}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info("Antwort unter %s gespeichert", path)
