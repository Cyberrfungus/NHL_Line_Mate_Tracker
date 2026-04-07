import { useState, useMemo } from "react";

// ─────────────────────────────────────────────────────────────────────────────
//  NHL DUO TRACKER
//  ── DAILY DATA ── Update this section each day via Artifact-Generator
// ─────────────────────────────────────────────────────────────────────────────

export const FETCH_TIME = "12:47 ET";

export const SEASON = {
  ELITE:    { W: 61,  L: 88,  CW: 30 },
  STRONG:   { W: 57,  L: 100, CW: 18 },
  "PP LINK":{ W: 90,  L: 142, CW: 42 },
};

export const GAME_ORDER = ["VAN@COL", "STL@LAK", "ANA@SJS"];

export const GAME_INFO = {
  "VAN@COL": {
    time: "8:30 PM",
    env: "HIGH",
    ou: "6.5",
    context: "COL 108 pts, Presidents' Trophy hunt · ⚠️ Makar OUT (UBI) → Toews assumes PP1 QB · VAN eliminated (last in NHL, 50 pts) · COL won 9-2 last game vs CGY",
  },
  "STL@LAK": {
    time: "9:00 PM",
    env: "HIGH",
    ou: "6.0",
    context: "LAK fighting for 2nd WC spot (29-26-18) · STL wild-card hunt (31-31-11, 4 pts back) · Two desperate teams · ⚠️ R.Thomas COLD FLAG — excluded",
  },
  "ANA@SJS": {
    time: "9:00 PM",
    env: "HIGH",
    ou: "6.5",
    context: "ANA 1st in Pacific (41-28-5) · SJS wild-card hunt (34-31-7, 2 pts back NAS) · SJS must win · Celebrini 101 pts milestone · ANA can clinch division",
  },
};

// ─────────────────────────────────────────────────────────────────────────────
//  STYLE CONSTANTS — fixed, do not edit daily
// ─────────────────────────────────────────────────────────────────────────────

export const MONO = {
  fontFamily: "'JetBrains Mono','Fira Code','Courier New',monospace",
};

export const TIER_CFG = {
  ELITE:    { bg: "#0F3D1E", bd: "#22C55E", tx: "#4ADE80" },
  STRONG:   { bg: "#0C2A4A", bd: "#3B82F6", tx: "#60A5FA" },
  "PP LINK":{ bg: "#3D2200", bd: "#F59E0B", tx: "#FBBF24" },
};

export const CORR_CFG = {
  Strongest:{ bg: "#052E16", bd: "#16A34A", tx: "#4ADE80" },
  High:     { bg: "#1C2A00", bd: "#84CC16", tx: "#A3E635" },
  Moderate: { bg: "#1C1800", bd: "#CA8A04", tx: "#FDE047" },
  Lowest:   { bg: "#2D0B0B", bd: "#DC2626", tx: "#FCA5A5" },
};

export const ENV_CFG = {
  HIGH: { tx: "#F97316", bd: "#F9731633" },
  MID:  { tx: "#FBBF24", bd: "#FBBF2433" },
  LOW:  { tx: "#60A5FA", bd: "#60A5FA33" },
};

export const TEAM_COL = {
  COL: "#7C3AED",
  VAN: "#22C55E",
  STL: "#3B82F6",
  LAK: "#94A3B8",
  ANA: "#FB923C",
  SJS: "#0EA5E9",
};

// ─────────────────────────────────────────────────────────────────────────────
//  HELPER COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

export function TierBadge({ tier }) {
  const t = TIER_CFG[tier] || {};
  return (
    <span style={{
      ...MONO,
      fontSize: 8,
      fontWeight: 800,
      padding: "2px 6px",
      borderRadius: 3,
      background: t.bg,
      border: `1px solid ${t.bd}`,
      color: t.tx,
      whiteSpace: "nowrap",
    }}>
      {tier}
    </span>
  );
}

export function CorrBadge({ corr }) {
  const c = CORR_CFG[corr] || {};
  return (
    <span style={{
      ...MONO,
      fontSize: 8,
      fontWeight: 700,
      padding: "2px 6px",
      borderRadius: 3,
      background: c.bg,
      border: `1px solid ${c.bd}`,
      color: c.tx,
      whiteSpace: "nowrap",
    }}>
      {corr}
    </span>
  );
}

export function StarBtn({ on, toggle }) {
  return (
    <button
      onClick={toggle}
      style={{
        background: "none",
        border: "none",
        cursor: "pointer",
        fontSize: 16,
        padding: "0 2px",
        color: on ? "#FCD34D" : "#334155",
        transition: "color 0.15s",
        lineHeight: 1,
      }}
    >
      {on ? "★" : "☆"}
    </button>
  );
}
