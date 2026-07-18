# 🎯 My Portfolio Candidate – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/manuematic/my_portfolio_candidate.svg)](https://github.com/manuematic/my_portfolio_candidate/releases)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

Eine Home Assistant Custom Integration zur Verwaltung von **Aktienkaufkandidaten**. Für jeden Kandidaten wird ein Zielkurs hinterlegt – sobald der aktuelle Kurs diesen Wert unterschreitet, wird eine Alarmierungsentität aktiv, die sich direkt in Automationen nutzen lässt. Kursdaten werden primär von der **ING Wertpapiere API** bezogen – zuverlässig, aktuell und ohne API-Key. Als Fallback steht **Yahoo Finance** zur Verfügung.

Gehört zur [my_portfolio](https://github.com/manuematic/my_portfolio)-Familie.

---

## ✨ Features

### Kursdaten
- 📡 **ING Wertpapiere API** als primäre Kursquelle (via ISIN, kein Key erforderlich)
- 📊 **Yahoo Finance** als Fallback – ideal für US-Aktien und ETFs
- ⚙️ **Datenquelle pro Kandidat** wählbar – ING und Yahoo lassen sich mischen
- 🕐 **Nur zu Börsenzeiten** – Kursabruf automatisch auf 09:00–20:00 MESZ begrenzt
- 🔄 **Automatische Aktualisierung** im konfigurierbaren Intervall (Standard: 15 Min.)

### Kandidaten-Verwaltung
- 📋 **Mehrere Listen** gleichzeitig verwaltbar
- ➕ Kandidaten vollständig über die **HA-Benutzeroberfläche** hinzufügen, bearbeiten, löschen
- 💾 **Persistente Speicherung** – Daten bleiben nach HA-Neustart erhalten

### Entitäten & Alarme
- 💹 **Kurs-Sensor** pro Kandidat – aktueller Kurs als Messwert (für Berechnungen nutzbar)
- 🔔 **Binary Sensor „Kurs unterschritten"** – `on` wenn aktueller Kurs ≤ Zielkurs
- 📉 **Differenz** zum Zielkurs – absolut in € und prozentual
- 📊 **Tagesperformance** absolut und prozentual

### Dashboard-Visualisierung
- 🃏 **Lovelace Custom Card** – keine externe Card-Library nötig
- Toggle zwischen **Alle Kandidaten** und **Nur Alarme**
- Farbkodierte Differenzanzeige (grün/gelb/rot je nach Abstand zum Zielkurs)
- Unterschrittene Kandidaten werden oben einsortiert

---

## 📋 Voraussetzungen

| Anforderung | Details |
|---|---|
| Home Assistant | Version 2024.1 oder neuer |
| HACS | Installiert und eingerichtet |
| Internetzugang | Für ING API und Yahoo Finance |
| ING API-Key | Nicht erforderlich |
| Yahoo API-Key | Nicht erforderlich |

---

## 🚀 Installation

### 1. Integration via HACS

1. HACS öffnen → **Integrationen** → **⋮** → **Benutzerdefinierte Repositories**
2. URL eingeben: `https://github.com/manuematic/my_portfolio_candidate`
3. Kategorie: **Integration** → **Hinzufügen**
4. Integration suchen: **My Portfolio Candidate** → **Installieren**
5. Home Assistant **neu starten**

### 2. Dashboard-Card installieren

1. Die Datei `www/my-portfolio-candidate/my-portfolio-candidate-card.js` nach `/config/www/my-portfolio-candidate/` kopieren
2. **Einstellungen → Dashboards → Ressourcen → + Ressource hinzufügen**
3. URL: `/local/my-portfolio-candidate/my-portfolio-candidate-card.js` → Typ: **JavaScript-Modul**

> **Tipp bei Updates:** Nach dem Ersetzen der `.js`-Datei den Browsercache umgehen,
> indem die Ressource-URL um eine Versionsnummer ergänzt wird: `/local/my-portfolio-candidate/my-portfolio-candidate-card.js?v=2`

---

## ⚙️ Einrichtung

1. **Einstellungen → Integrationen → + Integration hinzufügen**
2. Nach **„My Portfolio Candidate"** suchen und auswählen
3. Listen-Namen eingeben (z.B. „Meine Kaufkandidaten")
4. Standard-Kursquelle wählen (empfohlen: ING)
5. Aktualisierungsintervall wählen (Standard: 15 Minuten)

---

## 📥 Kandidaten verwalten

Alle Kandidaten werden direkt über die HA-Benutzeroberfläche verwaltet:

**Einstellungen → Integrationen → My Portfolio Candidate → Konfigurieren**

### Felder beim Hinzufügen

| Feld | Pflicht | Beschreibung |
|---|---|---|
| Bezeichnung | ✅ | Anzeigename (z.B. „SAP SE") |
| Kürzel (Yahoo) | ✅ | Börsenkürzel für Yahoo Finance (z.B. `SAP.DE`, `AAPL`) |
| Datenquelle | ✅ | **ING** (empfohlen) oder Yahoo Finance |
| ISIN | ✅ bei ING | z.B. `DE0007164600` für SAP |
| WKN | ☐ | z.B. `716460` (optional, nur zur Info) |
| Zielkurs | ✅ | Kaufkurs-Ziel in € – Alarm wird ausgelöst wenn Kurs ≤ Zielkurs |
| Memo-Zielkurs | ☐ | Reines Merkfeld (z.B. Zielkurs-Vorgabe von Börse Online), keine Alarm-Funktion |
| Memo-Stoppkurs | ☐ | Reines Merkfeld (z.B. Stoppkurs-Vorgabe von Börse Online), keine Alarm-Funktion |
| Notiz | ☐ | Freitext, max. 50 Zeichen, reine Merkfunktion ohne Alarm-Logik |

### Kürzel- und ISIN-Beispiele

| Aktie | ISIN (für ING) | Kürzel (für Yahoo) |
|---|---|---|
| SAP SE | `DE0007164600` | `SAP.DE` |
| BASF | `DE000BASF111` | `BAS.DE` |
| Apple | `US0378331005` | `AAPL` |
| Microsoft | `US5949181045` | `MSFT` |
| iShares DAX ETF | `DE0005933931` | `EXS1.DE` |
| Novo Nordisk | `DK0060534915` | `NVO` |

---

## 🃏 Dashboard-Card

```yaml
type: custom:my-portfolio-candidate-card
title: Kaufkandidaten        # optional, Standard: "My Portfolio Candidate"
```

### Card-Ansichten

Die Card hat einen Toggle-Button oben rechts:

| Ansicht | Inhalt |
|---|---|
| **Alle** | Alle Kandidaten mit aktuellem Kurs und Differenz zum Zielkurs |
| **Nur Alarm** | Nur Kandidaten deren Zielkurs bereits unterschritten wurde |

### Anzeige-Spalten

| Spalte | Beschreibung |
|---|---|
| Icon | 🔔 Alarm (Kurs unterschritten) / 📋 Normal |
| Aktie | Bezeichnung und Börsenkürzel |
| Ziel | Konfigurierter Zielkurs |
| Kurs | Aktueller Kurs |
| Differenz | Abstand zum Zielkurs in € und % (farbkodiert) |

**Farbkodierung der Differenz:**
- 🔴 Rot = Zielkurs unterschritten oder genau erreicht
- 🟡 Gelb = weniger als 5% über dem Zielkurs
- 🟢 Grün = mehr als 5% über dem Zielkurs

---

## 🔔 Automation-Beispiel: Kurs-Alarm

Der Binary Sensor `binary_sensor.<bezeichnung>_kurs_unterschritten` wechselt auf `on`,
sobald der aktuelle Kurs den Zielkurs erreicht oder unterschreitet.

```yaml
automation:
  alias: "Kaufkandidat – Zielkurs unterschritten"
  trigger:
    - platform: state
      entity_id: binary_sensor.sap_se_kurs_unterschritten
      to: "on"
  action:
    - service: notify.mobile_app
      data:
        title: "🎯 Kaufsignal!"
        message: >
          {{ state_attr('binary_sensor.sap_se_kurs_unterschritten', 'bezeichnung') }}
          hat den Zielkurs von
          {{ state_attr('binary_sensor.sap_se_kurs_unterschritten', 'zielkurs') }} €
          unterschritten. Aktueller Kurs:
          {{ state_attr('binary_sensor.sap_se_kurs_unterschritten', 'aktueller_kurs') }} €
```

---

## 📡 Datenquellen

| Quelle | Verwendung | API-Key | Hinweis |
|---|---|---|---|
| **ING Wertpapiere** | Aktuelle Kurse (Default) | Nein | Keine bekannte Begrenzung |
| **Yahoo Finance** | Kurse US-Aktien / Fallback | Nein | Inoffiziell, kann variieren |

---

## 🏷️ Entitäten & Attribute

### Sensor: Aktueller Kurs
Entitäts-ID: `sensor.<bezeichnung>`

| Attribut | Beschreibung |
|---|---|
| `bezeichnung` | Name des Kandidaten |
| `kuerzel` | Börsenkürzel (Yahoo) |
| `isin` | ISIN |
| `wkn` | WKN |
| `datenquelle` | `ing` oder `yahoo_finance` |
| `zielkurs` | Konfigurierter Zielkurs in € |
| `notiz` | Freitext-Notiz (max. 50 Zeichen), reine Merkfunktion ohne Alarm-Logik |
| `memo_zielkurs` | Merkfeld für einen Zielkurs (z.B. Börse Online), ohne Alarm-Logik |
| `memo_stoppkurs` | Merkfeld für einen Stoppkurs (z.B. Börse Online), ohne Alarm-Logik |
| `aktueller_kurs` | Aktueller Kurs in € |
| `differenz_abs` | Differenz: aktueller Kurs − Zielkurs in € |
| `differenz_pct` | Differenz in % |
| `kurs_unterschritten` | `true` wenn Kurs ≤ Zielkurs |
| `kurs_vortag` | Vortages-Schlusskurs |
| `tages_aenderung_abs` | Tagesveränderung in € |
| `tages_aenderung_pct` | Tagesveränderung in % |
| `liste` | Name der Kandidatenliste |

### Binary Sensor: Kurs unterschritten
Entitäts-ID: `binary_sensor.<bezeichnung>_kurs_unterschritten`

> Als Diagnose-Entität eingestuft – erscheint in der Geräteansicht unter „Diagnose" statt
> zusammen mit dem Kurs-Sensor, damit jede Aktie dort nur einmal auftaucht.

| Attribut | Beschreibung |
|---|---|
| `bezeichnung` | Name des Kandidaten |
| `kuerzel` | Börsenkürzel |
| `isin` | ISIN |
| `zielkurs` | Zielkurs in € |
| `notiz` | Freitext-Notiz (max. 50 Zeichen), reine Merkfunktion ohne Alarm-Logik |
| `memo_zielkurs` | Merkfeld für einen Zielkurs (z.B. Börse Online), ohne Alarm-Logik |
| `memo_stoppkurs` | Merkfeld für einen Stoppkurs (z.B. Börse Online), ohne Alarm-Logik |
| `aktueller_kurs` | Aktueller Kurs in € |
| `differenz_abs` | Differenz in € |
| `differenz_pct` | Differenz in % |
| `liste` | Name der Kandidatenliste |

---

## 🔗 Verwandt

- [my_portfolio](https://github.com/manuematic/my_portfolio) – Portfolio-Verwaltung mit Gewinn/Verlust, Analysten-Kursziele, Charts und mehr

---

## 📝 Lizenz

MIT License
