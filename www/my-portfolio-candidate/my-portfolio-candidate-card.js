/**
 * My Portfolio Candidate Card
 * Lovelace Custom Card für die my_portfolio_candidate Integration
 * Ablage: /config/www/my-portfolio-candidate/my-portfolio-candidate-card.js
 *
 * Toggle-Pattern identisch zu my-portfolio-daily-all-card.js
 */

const _candidateCardState = new Map();
let   _candidateCardUid   = 0;

class MyPortfolioCandidateCard extends HTMLElement {

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._uid = ++_candidateCardUid;
  }

  setConfig(config) {
    this._config = config;
    // State initialisieren – genau wie in daily-all-card
    if (!_candidateCardState.has(this._uid)) {
      _candidateCardState.set(this._uid, { showOnlyAlarm: false });
    }
  }

  // Getter/Setter identisch zum my_portfolio-Pattern
  get _showOnlyAlarm() {
    return (_candidateCardState.get(this._uid) || {}).showOnlyAlarm || false;
  }
  set _showOnlyAlarm(v) {
    const s = _candidateCardState.get(this._uid) || {};
    s.showOnlyAlarm = v;
    _candidateCardState.set(this._uid, s);
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  // Wird per onclick="this.getRootNode().host._toggle()" aufgerufen
  // – identisches Pattern wie _toggleSort() in my_portfolio
  _toggle() {
    this._showOnlyAlarm = !this._showOnlyAlarm;
    this._render();
  }

  getCardSize() { return 4; }

  _getKandidaten() {
    if (!this._hass) return [];
    const candidates = [];

    for (const [entityId, state] of Object.entries(this._hass.states)) {
      if (!state || !entityId.startsWith("binary_sensor.")) continue;
      const a = state.attributes || {};
      if (
        typeof a.zielkurs === "undefined" ||
        a.integration     !== "my_portfolio_candidate"
      ) continue;

      candidates.push({
        entityId,
        bezeichnung:    a.bezeichnung || a.kuerzel || entityId,
        kuerzel:        a.kuerzel || "",
        zielkurs:       a.zielkurs,
        aktuellerKurs:  a.aktueller_kurs,
        differenzAbs:   a.differenz_abs,
        differenzPct:   a.differenz_pct,
        unterschritten: state.state === "on",
      });
    }

    candidates.sort((a, b) => {
      if (a.unterschritten !== b.unterschritten) return a.unterschritten ? -1 : 1;
      return (a.differenzPct ?? 999) - (b.differenzPct ?? 999);
    });

    return candidates;
  }

  _fmt(val, dec = 2, suffix = "") {
    if (val == null) return "–";
    return Number(val).toFixed(dec) + suffix;
  }

  _diffColor(pct) {
    if (pct == null) return "var(--secondary-text-color)";
    if (pct <= 0)    return "var(--error-color,   #db4437)";
    if (pct <  5)    return "var(--warning-color, #ffa600)";
    return "var(--success-color, #43a047)";
  }

  _esc(str) {
    return String(str || "")
      .replace(/&/g,"&amp;").replace(/</g,"&lt;")
      .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }

  _render() {
    // Guard identisch zu daily-all-card
    if (!this._hass || !_candidateCardState.has(this._uid)) return;

    const config      = this._config || {};
    const title       = config.title || "Kaufkandidaten";
    const alle        = this._getKandidaten();
    const showAlarm   = this._showOnlyAlarm;
    const displayed   = showAlarm ? alle.filter(k => k.unterschritten) : alle;
    const countAll    = alle.length;
    const countAlarm  = alle.filter(k => k.unterschritten).length;
    const btnDisabled = countAlarm === 0 && !showAlarm;
    const btnLabel    = showAlarm ? `Alle anzeigen (${countAll})` : `Nur Alarm (${countAlarm})`;
    const btnClass    = "toggle-btn" + (showAlarm ? " active" : "") + (btnDisabled ? " tog-disabled" : "");

    const rows = displayed.map(k => {
      const color = this._diffColor(k.differenzPct);
      return `
        <tr class="${k.unterschritten ? 'alarm' : ''}">
          <td class="icon-col">${k.unterschritten ? '🔔' : '📋'}</td>
          <td class="name-col">
            <span class="bezeichnung">${this._esc(k.bezeichnung)}</span>
            <span class="kuerzel">${this._esc(k.kuerzel)}</span>
          </td>
          <td class="num-col ziel">${this._fmt(k.zielkurs,      2, " €")}</td>
          <td class="num-col kurs">${this._fmt(k.aktuellerKurs, 2, " €")}</td>
          <td class="num-col diff" style="color:${color}">
            ${this._fmt(k.differenzAbs, 2, " €")}<br>
            <span class="pct">${this._fmt(k.differenzPct, 2, "%")}</span>
          </td>
        </tr>`;
    }).join("");

    const emptyHint = displayed.length === 0
      ? `<tr><td colspan="5" class="empty">${
          showAlarm
            ? "Kein Kandidat hat aktuell den Zielkurs unterschritten."
            : "Noch keine Kaufkandidaten konfiguriert."
        }</td></tr>`
      : "";

    // innerHTML-Reset genau wie in my_portfolio-Cards
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { padding: 0; overflow: hidden; }
        .card-header {
          display: flex; align-items: center; justify-content: space-between;
          padding: 12px 16px 8px;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.12));
        }
        .card-header h2 {
          margin: 0; font-size: 1.1rem; font-weight: 500;
          color: var(--primary-text-color);
        }
        .badge-wrap { display: flex; align-items: center; gap: 8px; }
        .badge {
          display: inline-flex; align-items: center; justify-content: center;
          min-width: 22px; height: 22px; padding: 0 6px; border-radius: 11px;
          font-size: 0.75rem; font-weight: 600;
          background: var(--error-color, #db4437); color: #fff;
        }
        .badge.none { background: var(--secondary-text-color, #9e9e9e); }
        .toggle-btn {
          background: none;
          border: 1px solid var(--primary-color, #03a9f4);
          color: var(--primary-color, #03a9f4);
          border-radius: 12px; padding: 3px 10px; font-size: 0.75rem;
          cursor: pointer; white-space: nowrap; user-select: none;
          transition: background 0.2s, color 0.2s;
        }
        .toggle-btn:hover { background: var(--primary-color, #03a9f4); color: #fff; }
        .toggle-btn.active {
          background: var(--error-color, #db4437);
          border-color: var(--error-color, #db4437); color: #fff;
        }
        .toggle-btn.tog-disabled { opacity: 0.4; cursor: default; pointer-events: none; }
        table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
        thead th {
          padding: 6px 8px; text-align: right; font-size: 0.72rem; font-weight: 500;
          color: var(--secondary-text-color); text-transform: uppercase;
          letter-spacing: 0.03em;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.08));
        }
        thead th:first-child, thead th.name-col { text-align: left; }
        tbody tr {
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06));
          transition: background 0.15s;
        }
        tbody tr:last-child { border-bottom: none; }
        tbody tr:hover { background: var(--secondary-background-color, rgba(0,0,0,0.04)); }
        tbody tr.alarm { background: rgba(219,68,55,0.07); }
        tbody tr.alarm:hover { background: rgba(219,68,55,0.13); }
        td { padding: 8px; vertical-align: middle; }
        .icon-col { width: 28px; text-align: center; font-size: 1rem; padding-left: 10px; }
        .name-col { min-width: 100px; }
        .bezeichnung {
          display: block; font-weight: 500; color: var(--primary-text-color);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px;
        }
        .kuerzel { display: block; font-size: 0.72rem; color: var(--secondary-text-color); }
        .num-col { text-align: right; white-space: nowrap; padding-right: 12px; }
        .diff { font-weight: 600; font-size: 0.85rem; }
        .pct  { font-size: 0.72rem; font-weight: 400; }
        .kurs { color: var(--primary-text-color); }
        .ziel { color: var(--secondary-text-color); }
        .empty {
          text-align: center; padding: 24px;
          color: var(--secondary-text-color); font-style: italic;
        }
      </style>
      <ha-card>
        <div class="card-header">
          <h2>${this._esc(title)}</h2>
          <div class="badge-wrap">
            <span class="badge ${countAlarm === 0 ? 'none' : ''}">${countAlarm}</span>
            <button
              class="${btnClass}"
              onclick="this.getRootNode().host._toggle()"
            >${btnLabel}</button>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th></th><th class="name-col">Aktie</th>
              <th>Ziel</th><th>Kurs</th><th>Differenz</th>
            </tr>
          </thead>
          <tbody>${rows}${emptyHint}</tbody>
        </table>
      </ha-card>`;
  }

  static getStubConfig() { return { title: "Kaufkandidaten" }; }
}

customElements.define("my-portfolio-candidate-card", MyPortfolioCandidateCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type:        "my-portfolio-candidate-card",
  name:        "My Portfolio Candidate Card",
  description: "Zeigt Kaufkandidaten mit Zielkurs-Überwachung und Alarm-Markierung.",
  preview:     false,
});
