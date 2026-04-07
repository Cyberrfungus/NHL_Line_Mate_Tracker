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

// ─────────────────────────────────────────────────────────────────────────────
//  DUOS ARRAY — replace daily via Artifact-Generator
//  Fields: id, game, team, a, aPos, b, bPos, tier, conn, corr,
//          cold, invalid, top, rec, recR, note
// ─────────────────────────────────────────────────────────────────────────────

export const DUOS = [
  // ── VAN @ COL  8:30 PM ───────────────────────────────────────────────────
  { id:"c1", game:"VAN@COL", team:"COL", a:"MacKinnon", aPos:"C",  b:"Necas",     bPos:"RW",
    tier:"ELITE",    conn:"ES L1 + PP1",     corr:"Strongest", cold:false, invalid:false, top:true,
    rec:true,
    recR:"ELITE · MacKinnon–Necas L1+PP1 confirmed · Necas not blanked recently · Strongest · COL on fire (9-2 last game)",
    note:"COL's L1+PP1 duo. Necas 40+ pts RW on L1 with MacKinnon. MacKinnon 125 pts (2nd Art Ross). ⚠️ Makar OUT — PP1 QB structure shifts but both stay on PP1." },

  { id:"c2", game:"VAN@COL", team:"COL", a:"MacKinnon", aPos:"C",  b:"Landeskog", bPos:"LW",
    tier:"ELITE",    conn:"ES L1 + PP1/PP2", corr:"Strongest", cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Landeskog L1+PP2. MacKinnon L1+PP1. Double ES exposure but different PP units. ELITE by ES line." },

  { id:"c3", game:"VAN@COL", team:"COL", a:"Toews",     aPos:"D",  b:"MacKinnon", bPos:"C",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:true,
    rec:true,
    recR:"PP LINK F+D · ⭐ Toews steps into Makar's PP1 QB role tonight · MacKinnon PP1 C confirmed · neither blanked · High corr — new D-QB chain",
    note:"⭐ MAKAR OUT → Toews assumes PP1 QB. Toews→MacKinnon becomes COL's primary PP1 D-QB chain tonight." },

  { id:"c4", game:"VAN@COL", team:"COL", a:"Toews",     aPos:"D",  b:"Necas",     bPos:"RW",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Toews QB→Necas on PP1. Both PP1 unit. Toews absorbing Makar's minutes and QB role." },

  { id:"c5", game:"VAN@COL", team:"COL", a:"Burns",     aPos:"D",  b:"Landeskog", bPos:"LW",
    tier:"PP LINK",  conn:"PP2 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Burns QB→Landeskog PP2. Burns veteran QB on PP2 confirmed DFO." },

  { id:"c6", game:"VAN@COL", team:"COL", a:"Nelson",    aPos:"C",  b:"MacKinnon", bPos:"C",
    tier:"PP LINK",  conn:"PP1 F+F",         corr:"Lowest",    cold:false, invalid:false, top:false,
    rec:false, recR:"F+F — Lowest corr fails rule 4.",
    note:"Nelson + MacKinnon both PP1 but different ES lines (Nelson L2). PP-dependent, 5-player dilution." },

  { id:"c7", game:"VAN@COL", team:"COL", a:"Kadri",     aPos:"C",  b:"MacKinnon", bPos:"C",
    tier:"PP LINK",  conn:"PP1 F+F",         corr:"Lowest",    cold:false, invalid:false, top:false,
    rec:false, recR:"F+F — Lowest corr fails rule 4.",
    note:"Kadri + MacKinnon both PP1. Different ES lines (Kadri L3). PP-dependent." },

  { id:"c8", game:"VAN@COL", team:"COL", a:"Makar",     aPos:"D",  b:"MacKinnon", bPos:"C",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:true,  top:false,
    rec:false, recR:"",
    note:"⚠️ INVALID — Makar OUT tonight (upper-body injury, Bednar confirmed). DO NOT PLAY any Makar duo." },

  { id:"v1", game:"VAN@COL", team:"VAN", a:"Pettersson", aPos:"C", b:"Boeser",    bPos:"RW",
    tier:"PP LINK",  conn:"PP1 F+F",         corr:"Lowest",    cold:false, invalid:false, top:false,
    rec:false, recR:"F+F — Lowest corr. VAN eliminated — effort concern.",
    note:"E.Pettersson + Boeser both PP1 but different ES lines. VAN eliminated (50 pts) — low motivation risk." },

  { id:"v2", game:"VAN@COL", team:"VAN", a:"Hronek",    aPos:"D",  b:"Pettersson", bPos:"C",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"VAN eliminated — rule 4 motivation concern. Chain history untracked.",
    note:"Hronek QB→Pettersson PP1. VAN's primary D-QB chain. ⚠️ VAN eliminated — effort level unknown." },

  // ── STL @ LAK  9:00 PM ───────────────────────────────────────────────────
  { id:"s1", game:"STL@LAK", team:"STL", a:"Thomas",     aPos:"C",  b:"Holloway",   bPos:"LW",
    tier:"ELITE",    conn:"ES L1 + PP1",     corr:"Strongest", cold:true,  invalid:false, top:false,
    rec:false, recR:"⚠️ R.Thomas COLD FLAG — blanked 2+ consecutive games. EXCLUDED.",
    note:"❄️ COLD FLAG APPLIED — Thomas blanked 2+ consecutive games. Thomas+Holloway ELITE EXCLUDED until Thomas scores." },

  { id:"s2", game:"STL@LAK", team:"STL", a:"Thomas",     aPos:"C",  b:"Snuggerud",  bPos:"RW",
    tier:"STRONG",   conn:"ES L1",           corr:"Moderate",  cold:true,  invalid:false, top:false,
    rec:false, recR:"⚠️ R.Thomas COLD FLAG.",
    note:"❄️ COLD FLAG — Thomas EXCLUDED. Snuggerud on L1 RW with Thomas but cold flag blocks this play." },

  { id:"s3", game:"STL@LAK", team:"STL", a:"Broberg",    aPos:"D",  b:"Thomas",     bPos:"C",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:true,  invalid:false, top:false,
    rec:false, recR:"⚠️ R.Thomas COLD FLAG — chain blocked.",
    note:"❄️ COLD FLAG — Broberg QB→Thomas PP1 chain EXCLUDED. Thomas cold flag blocks this D-QB play." },

  { id:"s4", game:"STL@LAK", team:"STL", a:"Buchnevich", aPos:"LW", b:"Kyrou",      bPos:"RW",
    tier:"STRONG",   conn:"ES L2",           corr:"Moderate",  cold:false, invalid:false, top:true,
    rec:false, recR:"",
    note:"STL's L2 tandem. Buchnevich 70+ pts pace. Kyrou elite finisher. STL fighting for survival (4 pts back, wild card)." },

  { id:"s5", game:"STL@LAK", team:"STL", a:"Broberg",    aPos:"D",  b:"Buchnevich", bPos:"LW",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Broberg QB→Buchnevich on PP1 (Buchnevich on PP1 from L2 ES). D-QB chain structure valid." },

  { id:"s6", game:"STL@LAK", team:"STL", a:"Neighbours", aPos:"LW", b:"Buchnevich", bPos:"LW",
    tier:"PP LINK",  conn:"PP1 F+F",         corr:"Lowest",    cold:false, invalid:false, top:false,
    rec:false, recR:"F+F — Lowest corr fails rule 4.",
    note:"Both PP1, different ES lines. PP-dependent only." },

  { id:"l1", game:"STL@LAK", team:"LAK", a:"Panarin",    aPos:"LW", b:"Kopitar",    bPos:"C",
    tier:"ELITE",    conn:"ES L1 + PP1",     corr:"Strongest", cold:false, invalid:false, top:true,
    rec:false, recR:"LAK not tracked recent slates — chain overlap last 3 unconfirmed.",
    note:"LAK's L1+PP1 core. Panarin 40G pace, Kopitar elite playmaker. LAK fighting for WC (1 pt back Predators)." },

  { id:"l2", game:"STL@LAK", team:"LAK", a:"Clarke",     aPos:"D",  b:"Kopitar",    bPos:"C",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:true,
    rec:false, recR:"LAK not tracked recent slates.",
    note:"Clarke QB→Kopitar PP1. LAK's primary PP chain. Clarke breakout D season (50+ pts). ✓ DFO updated Mar 29." },

  { id:"l3", game:"STL@LAK", team:"LAK", a:"Clarke",     aPos:"D",  b:"Kempe",      bPos:"RW",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Clarke QB→Kempe one-timer slot PP1. Kempe 30+ goals, natural finisher in that slot." },

  { id:"l4", game:"STL@LAK", team:"LAK", a:"Clarke",     aPos:"D",  b:"Panarin",    bPos:"LW",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Clarke QB→Panarin net-front/mid slot on PP1. Both PP1 unit." },

  { id:"l5", game:"STL@LAK", team:"LAK", a:"Kopitar",    aPos:"C",  b:"Kempe",      bPos:"RW",
    tier:"ELITE",    conn:"ES L1 + PP1",     corr:"Strongest", cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Kopitar–Kempe L1+PP1 pair. Both high volume. Must-win context elevates effort." },

  { id:"l6", game:"STL@LAK", team:"LAK", a:"Doughty",    aPos:"D",  b:"Byfield",    bPos:"C",
    tier:"PP LINK",  conn:"PP2 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Doughty QB→Byfield PP2. Classic veteran D-QB→young star C. Doughty elite PP2 QB." },

  { id:"l7", game:"STL@LAK", team:"LAK", a:"Byfield",    aPos:"C",  b:"Moore",      bPos:"LW",
    tier:"STRONG",   conn:"ES L2",           corr:"Moderate",  cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Byfield–Moore L2 pair. Byfield breakout season at C. Moore speed on wing." },

  // ── ANA @ SJS  9:00 PM ───────────────────────────────────────────────────
  { id:"a1", game:"ANA@SJS", team:"ANA", a:"Carlsson",   aPos:"C",  b:"Kreider",   bPos:"LW",
    tier:"ELITE",    conn:"ES L1 + PP1",     corr:"Strongest", cold:false, invalid:false, top:true,
    rec:true,
    recR:"ELITE · Carlsson+Kreider L1+PP1 · ✅ DFO updated TODAY (Apr 1) · ANA 1st Pacific, fighting for division · Strongest corr",
    note:"ANA L1+PP1 pair. Carlsson elite young C (2nd overall pick 2023). Kreider 30G net-front vet. ✅ DFO page updated today — freshest data on the slate." },

  { id:"a2", game:"ANA@SJS", team:"ANA", a:"Carlsson",   aPos:"C",  b:"Terry",     bPos:"RW",
    tier:"STRONG",   conn:"ES L1",           corr:"Moderate",  cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Carlsson–Kreider–Terry L1 trio. Terry strong finisher on right wing." },

  { id:"a3", game:"ANA@SJS", team:"ANA", a:"J.Carlson",  aPos:"D",  b:"Carlsson",  bPos:"C",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:true,
    rec:true,
    recR:"PP LINK F+D · J.Carlson QB→L.Carlsson PP1 · ✅ DFO updated TODAY · L.Carlsson not blanked · High corr · D-QB chain confirmed",
    note:"J.Carlson (veteran D) QB→L.Carlsson (young star C) PP1. Perfect D-QB F+D structure. ✅ Confirmed from today's DFO." },

  { id:"a4", game:"ANA@SJS", team:"ANA", a:"J.Carlson",  aPos:"D",  b:"Terry",     bPos:"RW",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"J.Carlson QB→Terry one-timer on PP1. Both PP1. Terry natural finisher in that role." },

  { id:"a5", game:"ANA@SJS", team:"ANA", a:"J.Carlson",  aPos:"D",  b:"Kreider",   bPos:"LW",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"J.Carlson QB→Kreider net-front on PP1. Both PP1 unit." },

  { id:"a6", game:"ANA@SJS", team:"ANA", a:"Granlund",   aPos:"C",  b:"Carlsson",  bPos:"C",
    tier:"PP LINK",  conn:"PP1 F+F",         corr:"Lowest",    cold:false, invalid:false, top:false,
    rec:false, recR:"F+F — Lowest corr fails rule 4.",
    note:"Granlund + Carlsson both PP1. Granlund L2 ES, Carlsson L1. PP-dependent, 5-player dilution." },

  { id:"sj1", game:"ANA@SJS", team:"SJS", a:"Celebrini", aPos:"C",  b:"W.Smith",   bPos:"RW",
    tier:"ELITE",    conn:"ES L1 + PP1",     corr:"Strongest", cold:false, invalid:false, top:true,
    rec:true,
    recR:"ELITE · Celebrini+W.Smith L1+PP1 · Celebrini 101 pts milestone Mar 30 · neither blanked · Strongest · SJS must-win",
    note:"SJS L1+PP1. Celebrini 101 pts (6th teen in NHL history with 100+ pts). W.Smith L1 RW + PP1. SJS in wild-card hunt — maximum urgency tonight." },

  { id:"sj2", game:"ANA@SJS", team:"SJS", a:"Orlov",     aPos:"D",  b:"Celebrini", bPos:"C",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:true,
    rec:true,
    recR:"PP LINK F+D · Orlov QB→Celebrini PP1 · DFO updated Mar 31 (yesterday) · Celebrini hot/milestone · High corr",
    note:"Orlov QB→Celebrini — SJS primary PP1 D-QB chain. ✓ DFO updated yesterday. Celebrini on monster hot streak (101 pts)." },

  { id:"sj3", game:"ANA@SJS", team:"SJS", a:"Orlov",     aPos:"D",  b:"W.Smith",   bPos:"RW",
    tier:"PP LINK",  conn:"PP1 D-QB",        corr:"High",      cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Orlov QB→W.Smith PP1. Both PP1. W.Smith natural finisher on power play." },

  { id:"sj4", game:"ANA@SJS", team:"SJS", a:"Celebrini", aPos:"C",  b:"Chernyshov",bPos:"LW",
    tier:"STRONG",   conn:"ES L1",           corr:"Moderate",  cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Celebrini–Chernyshov L1 pair. Chernyshov scored GWG Mar 30. Both contributing." },

  { id:"sj5", game:"ANA@SJS", team:"SJS", a:"Wennberg",  aPos:"C",  b:"Eklund",    bPos:"LW",
    tier:"STRONG",   conn:"ES L2",           corr:"Moderate",  cold:false, invalid:false, top:false,
    rec:false, recR:"",
    note:"Wennberg–Eklund L2 pair. Wennberg PP1 C (cross-unit). Eklund PP2 LW." },

  { id:"sj6", game:"ANA@SJS", team:"SJS", a:"Wennberg",  aPos:"C",  b:"Toffoli",   bPos:"LW",
    tier:"PP LINK",  conn:"PP1 F+F",         corr:"Lowest",    cold:false, invalid:false, top:false,
    rec:false, recR:"F+F — Lowest corr fails rule 4.",
    note:"Both PP1. Wennberg L2 ES, Toffoli L3 ES. PP-dependent, 5-player dilution." },
];

// Recommended targets: pass all 4 rules (rec=true, not cold, not invalid)
export const REC = DUOS.filter(d => d.rec && !d.cold && !d.invalid);

// Kept as alias for GAME_ORDER for backwards compatibility
export const GAME_ORDER_LIST = GAME_ORDER;
