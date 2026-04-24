/**
 * Börsenkandidaten Card
 * Lovelace Custom Card für die boersen_kandidat Integration
 * Ablage: /config/www/boersen-kandidat/boersen-kandidat-card.js
 */

class BoersenKandidatCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._showOnlyUnterschritten = false;
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  // ── Hilfsfunktionen ───────────────────────────────────────────────────

  _getKandidaten() {
    if (!this._hass) return [];

    const candidates = [];
    const states = this._hass.states;

    for (const entityId of Object.keys(states)) {
      const state = states[entityId];
      if (!state) continue;

      // Binary Sensor: Kurs unterschritten
      if (
        entityId.startsWith("binary_sensor.") &&
        state.attributes &&
        typeof state.attributes.zielkurs !== "undefined" &&
        typeof state.attributes.aktueller_kurs !== "undefined"
      ) {
        const attrs = state.attributes;
        candidates.push({
          entityId,
          bezeichnung: attrs.bezeichnung || attrs.kuerzel || entityId,
          kuerzel: attrs.kuerzel || "",
          isin: attrs.isin || "",
          zielkurs: attrs.zielkurs,
          aktuellerKurs: attrs.aktueller_kurs,
          differenzAbs: attrs.differenz_abs,
          differenzPct: attrs.differenz_pct,
          unterschritten: state.state === "on",
        });
      }
    }

    // Sortierung: Unterschrittene zuerst, dann nach Differenz-% aufsteigend
    candidates.sort((a, b) => {
      if (a.unterschritten && !b.unterschritten) return -1;
      if (!a.unterschritten && b.unterschritten) return 1;
      const pa = a.differenzPct ?? 999;
      const pb = b.differenzPct ?? 999;
      return pa - pb;
    });

    return candidates;
  }

  _fmt(val, decimals = 2, suffix = "") {
    if (val === null || val === undefined) return "–";
    return Number(val).toFixed(decimals) + suffix;
  }

  _diffColor(pct) {
    if (pct === null || pct === undefined) return "var(--secondary-text-color)";
    if (pct <= 0) return "var(--error-color, #db4437)";
    if (pct < 5) return "var(--warning-color, #ffa600)";
    return "var(--success-color, #43a047)";
  }

  // ── Template ──────────────────────────────────────────────────────────

  _render() {
    if (!this.shadowRoot) return;

    const alle = this._getKandidaten();
    const toggle = this._showOnlyUnterschritten;
    const displayed = toggle ? alle.filter((k) => k.unterschritten) : alle;

    const countAll = alle.length;
    const countAlarm = alle.filter((k) => k.unterschritten).length;

    const title = this._config.title || "Börsenkandidaten";

    const rows = displayed.map((k) => {
      const alarmClass = k.unterschritten ? "alarm" : "";
      const alarmIcon = k.unterschritten ? "🔔" : "📋";
      const diffPctStr = this._fmt(k.differenzPct, 2, "%");
      const diffAbsStr = this._fmt(k.differenzAbs, 2, " €");
      const kursStr = this._fmt(k.aktuellerKurs, 2, " €");
      const zielStr = this._fmt(k.zielkurs, 2, " €");
      const color = this._diffColor(k.differenzPct);

      return `
        <tr class="${alarmClass}">
          <td class="icon-col">${alarmIcon}</td>
          <td class="name-col">
            <span class="bezeichnung">${this._esc(k.bezeichnung)}</span>
            <span class="kuerzel">${this._esc(k.kuerzel)}</span>
          </td>
          <td class="num-col ziel">${zielStr}</td>
          <td class="num-col kurs">${kursStr}</td>
          <td class="num-col diff" style="color:${color}">
            ${diffAbsStr}<br>
            <span class="pct">${diffPctStr}</span>
          </td>
        </tr>
      `;
    }).join("");

    const emptyHint = displayed.length === 0
      ? `<tr><td colspan="5" class="empty">
          ${toggle ? "Kein Kandidat hat aktuell den Zielkurs unterschritten." : "Noch keine Kaufkandidaten konfiguriert."}
         </td></tr>`
      : "";

    const toggleLabel = toggle
      ? `Alle anzeigen (${countAll})`
      : `Nur Alarm (${countAlarm})`;

    const toggleDisabled = countAlarm === 0 && !toggle ? "disabled" : "";

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          padding: 0;
          overflow: hidden;
        }
        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px 8px;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.12));
        }
        .card-header h2 {
          margin: 0;
          font-size: 1.1rem;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        .badge-wrap {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 22px;
          height: 22px;
          padding: 0 6px;
          border-radius: 11px;
          font-size: 0.75rem;
          font-weight: 600;
          background: var(--error-color, #db4437);
          color: #fff;
        }
        .badge.none {
          background: var(--secondary-text-color, #9e9e9e);
        }
        .toggle-btn {
          background: none;
          border: 1px solid var(--primary-color, #03a9f4);
          color: var(--primary-color, #03a9f4);
          border-radius: 12px;
          padding: 3px 10px;
          font-size: 0.75rem;
          cursor: pointer;
          white-space: nowrap;
          transition: background 0.2s, color 0.2s;
        }
        .toggle-btn:hover:not([disabled]) {
          background: var(--primary-color, #03a9f4);
          color: #fff;
        }
        .toggle-btn[disabled] {
          opacity: 0.4;
          cursor: default;
        }
        .toggle-btn.active {
          background: var(--error-color, #db4437);
          border-color: var(--error-color, #db4437);
          color: #fff;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.88rem;
        }
        thead th {
          padding: 6px 8px;
          text-align: right;
          font-size: 0.72rem;
          font-weight: 500;
          color: var(--secondary-text-color);
          text-transform: uppercase;
          letter-spacing: 0.03em;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.08));
        }
        thead th:first-child,
        thead th.name-col {
          text-align: left;
        }
        tbody tr {
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06));
          transition: background 0.15s;
        }
        tbody tr:last-child {
          border-bottom: none;
        }
        tbody tr:hover {
          background: var(--secondary-background-color, rgba(0,0,0,0.04));
        }
        tbody tr.alarm {
          background: rgba(219, 68, 55, 0.07);
        }
        tbody tr.alarm:hover {
          background: rgba(219, 68, 55, 0.13);
        }
        td {
          padding: 8px 8px;
          vertical-align: middle;
        }
        .icon-col {
          width: 28px;
          text-align: center;
          font-size: 1rem;
          padding-left: 10px;
        }
        .name-col {
          min-width: 100px;
        }
        .bezeichnung {
          display: block;
          font-weight: 500;
          color: var(--primary-text-color);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 160px;
        }
        .kuerzel {
          display: block;
          font-size: 0.72rem;
          color: var(--secondary-text-color);
        }
        .num-col {
          text-align: right;
          white-space: nowrap;
          padding-right: 12px;
        }
        .diff {
          font-weight: 600;
          font-size: 0.85rem;
        }
        .pct {
          font-size: 0.72rem;
          font-weight: 400;
        }
        .kurs {
          color: var(--primary-text-color);
        }
        .ziel {
          color: var(--secondary-text-color);
        }
        .empty {
          text-align: center;
          padding: 24px;
          color: var(--secondary-text-color);
          font-style: italic;
        }
      </style>

      <ha-card>
        <div class="card-header">
          <h2>${this._esc(title)}</h2>
          <div class="badge-wrap">
            <span class="badge ${countAlarm === 0 ? 'none' : ''}">${countAlarm}</span>
            <button
              class="toggle-btn ${toggle ? 'active' : ''}"
              id="toggle-btn"
              ${toggleDisabled}
            >${toggleLabel}</button>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th></th>
              <th class="name-col">Aktie</th>
              <th>Ziel</th>
              <th>Kurs</th>
              <th>Differenz</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
            ${emptyHint}
          </tbody>
        </table>
      </ha-card>
    `;

    // Toggle Button Event
    const btn = this.shadowRoot.getElementById("toggle-btn");
    if (btn && !btn.disabled) {
      btn.addEventListener("click", () => {
        this._showOnlyUnterschritten = !this._showOnlyUnterschritten;
        this._render();
      });
    }
  }

  _esc(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

customElements.define("boersen-kandidat-card", BoersenKandidatCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "boersen-kandidat-card",
  name: "Börsenkandidaten Card",
  description: "Zeigt Kaufkandidaten mit Zielkurs-Überwachung und Alarm-Markierung.",
  preview: false,
});
