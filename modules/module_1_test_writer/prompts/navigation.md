Hier ist die Navigationsstruktur der Anwendung im JSON-Format, die du zwingend berücksichtigen musst:

### DEINE REGELN FÜR DIE TESTERSTELLUNG:

1. **Navigations-Logik:** orientiere den Benutzer mit dem Navigationspfad (z. B, )

2. **Abhängigkeiten prüfen (Voraussetzungen):**
   Prüfe im JSON das Feld "requires". Wenn eine User Story eine Maske betrifft, die eine Voraussetzung hat (z. B. "Zeiträume festlegen"), MUSS dein Testfall mit den Schritten beginnen, die diese Voraussetzung erfüllen, auch wenn dies nicht explizit in der User Story steht.

3. **Status der Anwendung:**
   Beachte den "application_context". Wenn dort steht, dass eine Steuernummer ausgewählt sein muss, muss dies der erste Schritt in jedem Testskript sein.

### Navigationsstruktur in JSON Format###
[
    {
        "application_context": "Nachrichten",
        "root_requirement": null,
        "navigation_tree": null
    },
    {
        "application_context": "Prüfungen",
        "root_requirement": "Diese Seite wird erst nach Auswahl einer Prüfungsnummer aus dem Prüfungsplan angezeigt",
        "navigation_tree": [
            {
                "label": "Fallinformationen",
                "submenus": null
            },
            {
                "label": "Prüfungsdetails",
                "submenus": null
            },
            {
                "label": "Kontaktinformationen",
                "submenus": null
            },
            {
                "label": "Verlauf",
                "submenus": null
            },
            {
                "label": "Vorbereitung",
                "submenus": [
                    {
                        "label": "Zeiträume",
                        "submenus": null,
                        "requires": null
                    },
                    {
                        "label": "Festsetzungsdaten",
                        "requires": "Festlegung von Prüfungszeitraum (Von- Bis) und Sichtungszeitraum (Von- Bis) in 'Zeiträume'",
                        "submenus": null
                    },
                    {
                        "label": "Gewinnermittlung",
                        "requires": "Festlegung von Prüfungszeitraum (Von- Bis) und Sichtungszeitraum (Von- Bis) in 'Zeiträume'",
                        "submenus": [
                            {
                                "label": "E-Bilanz Ansicht",
                                "submenus": null
                            },
                            {
                                "label": "Steuerbilanz",
                                "submenus": null
                            },
                            {
                                "label": "E-Gewinn- und Verlustrechnung",
                                "submenus": null
                            },
                            {
                                "Epic": "Kapitalkontenentwicklung",
                                "label": "Kapitalkontenentwicklung",
                                "submenus": null
                            },
                            {
                                "Epic": "EÜR",
                                "label": "Betriebsvermögensvergleich",
                                "submenus": null
                            },
                            {
                                "label": "EÜR",
                                "requires": "Diese Seite wird erst nach Auswahl der Gewinnermittlungsart 'Gewinnermittlung § 4 Abs. 3 EStG' in der Maske 'Zeiträume' angezeig",
                                "submenus": null
                            }
                        ]
                    },
                    {
                        "label": "Steuerabgleich vor Prüfung",
                        "submenus": null
                    },
                    {
                        "label": "Anordnung",
                        "submenus": null
                    }
                ]
            },
            {
                "label": "Durchführung",
                "requires": "Festlegung von Prüfungszeitraum (Von- Bis) und Sichtungszeitraum (Von- Bis) in 'Zeiträume'",
                "submenus": [
                    {
                        "label": "Prüfungsfeststellungen",
                        "submenus": null
                    },
                    {
                        "label": "Hebeberechtigte Gemeinden",
                        "submenus": null
                    },
                    {
                        "label": "Steuer-/Rückstellungsberechnung",
                        "submenus": null
                    },
                    {
                        "label": "Mehr- und Wenigerrechnung",
                        "requires": "Festlegung von 'Gewinnermittlungsart' auf 'Bilanzierung' in der Maske 'Zeiträume'",
                        "submenus": null
                    },
                    {
                        "label": "Gewinnermittlung",
                        "submenus":  "submenus": [
                            {
                                "Epic": "Kapitalkontenentwicklung lt. Prüfung",
                                "label": "Kapitalkontenentwicklung",
                                "submenus": null
                            }
                        ]
                    },
                    {
                        "label": "Schlussbesprechung",
                        "submenus": null
                    }
                ]
            },
            {
                "label": "Abwicklung",
                "requires": "Festlegung von Prüfungszeitraum (Von- Bis) und Sichtungszeitraum (Von- Bis) in 'Zeiträume'",
                "submenus": [
                    {
                        "label": "Zusammenfassung der Steuerarten",
                        "requires": "Benötigt Sichtungszeitraum, Gewinnermittlungsart, Einkunftsart, Wirtschaftsjahre und Prüfungszeitraum",
                        "submenus": null
                    },
                    {
                        "label": "Körperschaftsteuer",
                        "requires": "Prüfungskategorie = Kapitalgesellschaft, Prüfungszeitraum gesetzt, mindestens ein KB der KBGroup 'KST' im Prüfungszeitraum",
                        "submenus": null
                    },
                    {
                        "label": "Umsatzsteuer",
                        "requires": "Prüfungskategorie = Einzelunternehmen, Prüfungszeitraum gesetzt, mindestens ein KB der KBGroup 'EST' im Prüfungszeitraum",
                        "submenus": null
                    },
                    {
                        "label": "Gewerbesteuer",
                        "requires": "Prüfungszeitraum gesetzt, mindestens ein KB der KBGroup 'GEWST' im Prüfungszeitraum",
                        "submenus": null
                    },
                    {
                        "label": "Ergebnisse",
                        "requires": "Prüfungsnummer mit Status beendet oder Begonnen",
                        "submenus": null
                    },
                    {
                        "label": "Berichte",
                        "requires": "Prüfungsnummer oder  aus dem Prüfungsplan mit dem Status beendet",
                        "submenus": [
                            {
                                "label": "Manueller Bericht",
                                "beschreibung": "hier steht die Aktionen <PDF Generieren> und <Zur Zeichnung vorlegen> zu Verfügung",
                                "Tabs": [
                                    {
                                        "label": "Manueller Bericht",
                                        "submenus": null
                                    },
                                    {
                                        "label": "Stellungnahme",
                                        "submenus": null
                                    },
                                    {
                                        "label": "Übermittlungsschreiben",
                                        "submenus": null
                                    }
                                ]
                            },
                            {
                                "label": "Mitteilung über ergebnislose Bp",
                                "beschreibung": "hier steht die Aktionen <PDF Generieren> und <Zur Zeichnung vorlegen> zu Verfügung",
                                "Tabs": [
                                    {
                                        "label": "Eingabedialog",
                                        "submenus": null
                                    },
                                    {
                                        "label": "Übermittlungsschreiben",
                                        "submenus": null
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "label": "Auswertung",
                        "submenus": null
                    }
                ]
            },
            {
                "label": "Prüfungsinformationen",
                "submenus": null
            },
            {
                "label": "Bemerkungen",
                "submenus": null
            }
        ]
    }

]