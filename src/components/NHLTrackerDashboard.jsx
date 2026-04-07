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

// ─────────────────────────────────────────────────────────────────────────────
//  APP COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export default function App() {

  // ── Filter state ──────────────────────────────────────────────────────────
  const [tierF,   setTierF]  = useState("ALL");
  const [teamF,   setTeamF]  = useState("ALL");
  const [gameF,   setGameF]  = useState("ALL");
  const [corrF,   setCorrF]  = useState("ALL");
  const [search,  setSearch] = useState("");
  const [betsOnly, setBets]  = useState(false);

  // ── Bet tracking: Set of duo IDs ──────────────────────────────────────────
  const [myBets, setMyBets] = useState(new Set());

  // ── Collapsed game blocks: keyed by game string ───────────────────────────
  const [collapsed, setColl] = useState({
    "VAN@COL": false,
    "STL@LAK": true,
    "ANA@SJS": true,
  });

  // ── Toggle helpers ────────────────────────────────────────────────────────
  const toggleBet = (id) =>
    setMyBets((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const toggleCol = (game) =>
    setColl((prev) => ({ ...prev, [game]: !prev[game] }));

  // ── Derived: unique sorted team list ─────────────────────────────────────
  const teams = useMemo(
    () => [...new Set(DUOS.map((d) => d.team))].sort(),
    []
  );

  // ── Derived: filtered duo list ────────────────────────────────────────────
  const filtered = useMemo(() => {
    return DUOS.filter((d) => {
      if (betsOnly && !myBets.has(d.id))                          return false;
      if (tierF !== "ALL" && d.tier !== tierF)                    return false;
      if (teamF !== "ALL" && d.team !== teamF)                    return false;
      if (gameF !== "ALL" && d.game !== gameF)                    return false;
      if (corrF !== "ALL" && d.corr !== corrF)                    return false;
      if (search) {
        const q = search.toLowerCase();
        if (
          !d.a.toLowerCase().includes(q) &&
          !d.b.toLowerCase().includes(q) &&
          !d.team.toLowerCase().includes(q)
        ) return false;
      }
      return true;
    });
  }, [tierF, teamF, gameF, corrF, search, betsOnly, myBets]);

  // ── Derived: starred duos for My Bets panel ───────────────────────────────
  const betDuos = DUOS.filter((d) => myBets.has(d.id));

  // ── Derived: active duo counts per tier (excl. invalid + cold) ───────────
  const counts = useMemo(() => {
    const c = { ELITE: 0, STRONG: 0, "PP LINK": 0 };
    DUOS.filter((d) => !d.invalid && !d.cold).forEach((d) => c[d.tier]++);
    return c;
  }, []);

  // ── Derived: any filter active? ───────────────────────────────────────────
  const hasFilter =
    tierF !== "ALL" ||
    teamF !== "ALL" ||
    gameF !== "ALL" ||
    corrF !== "ALL" ||
    search !== "" ||
    betsOnly;

  // ── Btn: reusable filter toggle button ────────────────────────────────────
  const Btn = ({ v, cur, set, col }) => (
    <button
      onClick={() => set((x) => (x === v ? "ALL" : v))}
      style={{
        ...MONO,
        fontSize: 8,
        fontWeight: 700,
        padding: "4px 9px",
        borderRadius: 4,
        cursor: "pointer",
        border: "1px solid",
        background: cur === v ? (col || "#1E293B") : "transparent",
        borderColor: cur === v ? (col || "#475569") : "#1E293B",
        color: cur === v ? "#F8FAFC" : "#475569",
      }}
    >
      {v}
    </button>
  );

  // ── Row: renders a single duo entry ─────────────────────────────────────
  const Row = ({ d }) => {
    const on    = myBets.has(d.id);
    const tc    = TIER_CFG[d.tier];
    const isRec = REC.some((r) => r.id === d.id);

    // Row background: invalid > cold > starred > recommended > default
    const rowBg =
      d.invalid ? "#1A1000" :
      d.cold    ? "#1A0808" :
      on        ? "#0C0800" :
      d.rec     ? "#050E07" :
      "transparent";

    // Left border color signals state at a glance
    const lBorder =
      d.invalid ? "#78350F" :
      d.cold    ? "#7F1D1D" :
      on        ? "#92400E" :
      isRec     ? "#16A34A" :
      tc.bd + "33";

    return (
      <div style={{
        display: "grid",
        gridTemplateColumns: "30px 58px 1fr 1fr 88px 80px 96px 1fr",
        padding: "7px 10px",
        borderBottom: "1px solid #06080F",
        background: rowBg,
        borderLeft: `3px solid ${lBorder}`,
      }}>
        {/* Col 1: Star / warning icon */}
        <div style={{ display:"flex", alignItems:"center", justifyContent:"center" }}>
          {d.invalid
            ? <span style={{ fontSize:9, color:"#F59E0B" }}>⚠️</span>
            : d.cold
            ? <span style={{ fontSize:9, color:"#EF4444" }}>❄️</span>
            : <StarBtn on={on} toggle={() => toggleBet(d.id)} />}
        </div>

        {/* Col 2: Team + recommended flag */}
        <div style={{ display:"flex", alignItems:"center", gap:3 }}>
          <span style={{ ...MONO, fontSize:11, fontWeight:800, color: TEAM_COL[d.team] || "#fff" }}>
            {d.team}
          </span>
          {isRec && <span style={{ fontSize:9, color:"#4ADE80" }}>🎯</span>}
        </div>

        {/* Col 3: Player A + position */}
        <div style={{ display:"flex", alignItems:"center", gap:4 }}>
          <span style={{ ...MONO, fontSize:11, fontWeight:700, color: d.invalid || d.cold ? "#FCA5A5" : "#F8FAFC" }}>
            {d.a}
          </span>
          <span style={{ fontSize:8, color:"#475569" }}>{d.aPos}</span>
        </div>

        {/* Col 4: Player B + position */}
        <div style={{ display:"flex", alignItems:"center", gap:4 }}>
          <span style={{ ...MONO, fontSize:11, fontWeight:700, color: d.invalid || d.cold ? "#FCA5A5" : "#F8FAFC" }}>
            {d.b}
          </span>
          <span style={{ fontSize:8, color:"#475569" }}>{d.bPos}</span>
        </div>

        {/* Col 5: Tier badge */}
        <div style={{ display:"flex", alignItems:"center" }}>
          <TierBadge tier={d.tier} />
        </div>

        {/* Col 6: Connection type */}
        <div style={{ display:"flex", alignItems:"center" }}>
          <span style={{ fontSize:9, color:"#94A3B8" }}>{d.conn}</span>
        </div>

        {/* Col 7: Correlation badge */}
        <div style={{ display:"flex", alignItems:"center" }}>
          <CorrBadge corr={d.corr} />
        </div>

        {/* Col 8: Notes */}
        <div style={{
          fontSize: 9.5,
          color: d.invalid || d.cold ? "#FCA5A5" : "#CBD5E1",
          lineHeight: 1.45,
          display: "flex",
          alignItems: "center",
        }}>
          {d.note}
        </div>
      </div>
    );
  };

  // ── JSX ───────────────────────────────────────────────────────────────────
  return (
    <div style={{ background:"#04060C", minHeight:"100vh", color:"#E2E8F0", ...MONO, padding:"14px 12px", maxWidth:1360, margin:"0 auto" }}>

      {/* ── HEADER ────────────────────────────────────────────────────────── */}
      <div style={{ borderBottom:"2px solid #1E293B", paddingBottom:12, marginBottom:12 }}>
        <div style={{ fontSize:8, color:"#334155", letterSpacing:3, marginBottom:3 }}>
          NHL DUO TRACKER · ANDY FRANCES METHODOLOGY · PRE-GAME
        </div>
        <div style={{ fontSize:22, fontWeight:900, color:"#F8FAFC", letterSpacing:2 }}>
          NHL DUO TRACKER APR 01 2026
        </div>
        <div style={{ fontSize:10, color:"#4ADE80", marginTop:3, fontStyle:"italic" }}>
          Lines gathered at {FETCH_TIME} from Daily Faceoff
        </div>
        <div style={{ fontSize:10, color:"#64748B", marginTop:2 }}>
          {GAME_ORDER.length} games · {[...new Set(DUOS.map(d => d.team))].length} teams · {DUOS.filter(d => !d.invalid && !d.cold).length} active duos · {REC.length} recommended targets
        </div>

        {/* Stat boxes */}
        <div style={{ display:"flex", gap:8, marginTop:10, flexWrap:"wrap" }}>
          {[
            ["ELITE",     counts.ELITE,    "#4ADE80", "#0F3D1E", "#22C55E"],
            ["STRONG",    counts.STRONG,   "#60A5FA", "#0C2A4A", "#3B82F6"],
            ["PP LINK",   counts["PP LINK"],"#FBBF24","#3D2200", "#F59E0B"],
            ["🎯 TARGETS",REC.length,      "#A3E635", "#1C2A00", "#84CC16"],
            ["★ BETS",    myBets.size,     "#FCD34D", "#120A00", "#92400E"],
          ].map(([label, val, tx, bg, bd]) => (
            <div key={label} style={{ padding:"6px 12px", background:bg, border:`1px solid ${bd}`, borderRadius:6 }}>
              <div style={{ fontSize:7, color:bd, letterSpacing:1 }}>{label}</div>
              <div style={{ fontSize:18, fontWeight:900, color:tx }}>{val}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── RECOMMENDED TARGETS ───────────────────────────────────────────── */}
      <div style={{ background:"#030C07", border:"2px solid #16A34A", borderRadius:10, padding:"12px 14px", marginBottom:13 }}>

        {/* Title row */}
        <div style={{ display:"flex", alignItems:"center", gap:9, marginBottom:9 }}>
          <span style={{ fontSize:14, fontWeight:900, color:"#4ADE80" }}>🎯 RECOMMENDED TARGETS</span>
          <span style={{ fontSize:8, color:"#16A34A", background:"#052E16", padding:"2px 9px", borderRadius:4, border:"1px solid #16A34A" }}>
            {REC.length} duos pass all 4 rules
          </span>
        </div>

        {/* 4 rules */}
        <div style={{ fontSize:8, color:"#4ADE80", marginBottom:9, opacity:0.75, lineHeight:1.7 }}>
          ① ELITE or PP LINK &nbsp;·&nbsp; ② Neither player blanked last 2 games &nbsp;·&nbsp;
          ③ Chain overlap or validated D-QB in last 3 slates &nbsp;·&nbsp; ④ Corr = Strongest or High
        </div>

        {/* Table header */}
        <div style={{ display:"grid", gridTemplateColumns:"64px 1fr 1fr 88px 96px 1fr",
          background:"#041409", borderBottom:"1px solid #14532D", padding:"4px 10px", borderRadius:"4px 4px 0 0" }}>
          {["TEAM/GAME","PLAYER A","PLAYER B","TIER","CORR","REASON"].map((h, i) => (
            <div key={i} style={{ fontSize:7, color:"#16A34A", fontWeight:700 }}>{h}</div>
          ))}
        </div>

        {/* Target rows */}
        {REC.map((d, i) => {
          const [aw, hw] = d.game.split("@");
          const on = myBets.has(d.id);
          return (
            <div key={d.id} style={{
              display: "grid",
              gridTemplateColumns: "64px 1fr 1fr 88px 96px 1fr",
              padding: "9px 10px",
              borderBottom: "1px solid #0A1A0A",
              background: on ? "#0A1400" : i % 2 === 0 ? "#050E08" : "#060F09",
              borderLeft: `3px solid ${on ? "#FCD34D" : "#16A34A"}`,
            }}>
              {/* Team + game */}
              <div style={{ display:"flex", flexDirection:"column", gap:2, justifyContent:"center" }}>
                <span style={{ fontSize:8, fontWeight:800, color: TEAM_COL[d.team] || "#fff" }}>{d.team}</span>
                <span style={{ fontSize:7, color:"#475569" }}>{aw}@{hw}</span>
              </div>
              {/* Player A */}
              <div style={{ display:"flex", alignItems:"center", gap:5 }}>
                <span style={{ fontSize:11, fontWeight:700, color:"#F8FAFC" }}>{d.a}</span>
                <span style={{ fontSize:8, color:"#475569" }}>{d.aPos}</span>
                <StarBtn on={on} toggle={() => toggleBet(d.id)} />
              </div>
              {/* Player B */}
              <div style={{ display:"flex", alignItems:"center", gap:5 }}>
                <span style={{ fontSize:11, fontWeight:700, color:"#F8FAFC" }}>{d.b}</span>
                <span style={{ fontSize:8, color:"#475569" }}>{d.bPos}</span>
              </div>
              {/* Tier */}
              <div style={{ display:"flex", alignItems:"center" }}>
                <TierBadge tier={d.tier} />
              </div>
              {/* Corr */}
              <div style={{ display:"flex", alignItems:"center" }}>
                <CorrBadge corr={d.corr} />
              </div>
              {/* Reason */}
              <div style={{ fontSize:9, color:"#86EFAC", lineHeight:1.5, display:"flex", alignItems:"center" }}>
                {d.recR}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── MY BETS ───────────────────────────────────────────────────────── */}
      {betDuos.length > 0 && (
        <div style={{ background:"#120A00", border:"2px solid #92400E", borderRadius:8, padding:"10px 12px", marginBottom:12 }}>
          {/* Title row */}
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:8 }}>
            <span style={{ fontSize:12, fontWeight:900, color:"#FCD34D" }}>★ MY BETS</span>
            <span style={{ fontSize:9, color:"#92400E" }}>
              {betDuos.length} duo{betDuos.length > 1 ? "s" : ""} selected
            </span>
            <button
              onClick={() => setBets(v => !v)}
              style={{
                ...MONO, fontSize:8, fontWeight:700, padding:"3px 9px", borderRadius:4,
                cursor:"pointer", border:"1px solid",
                background: betsOnly ? "#1C0A00" : "transparent",
                borderColor: betsOnly ? "#F59E0B" : "#334155",
                color: betsOnly ? "#FCD34D" : "#475569",
                marginLeft:6,
              }}
            >
              BETS ONLY {betsOnly ? "ON" : "OFF"}
            </button>
          </div>

          {/* Bet pills */}
          <div style={{ display:"flex", flexWrap:"wrap", gap:6 }}>
            {betDuos.map(d => {
              const tc = TIER_CFG[d.tier];
              return (
                <div key={d.id} style={{
                  display:"flex", alignItems:"center", gap:6,
                  padding:"5px 10px", background:"#1A0F00",
                  border:`1px solid ${tc.bd}`, borderRadius:5,
                }}>
                  <span style={{ fontSize:9, fontWeight:800, color: TEAM_COL[d.team] || "#fff" }}>{d.team}</span>
                  <span style={{ fontSize:11, fontWeight:700, color:"#F8FAFC" }}>{d.a} + {d.b}</span>
                  <TierBadge tier={d.tier} />
                  <CorrBadge corr={d.corr} />
                  <StarBtn on={true} toggle={() => toggleBet(d.id)} />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── FILTERS ───────────────────────────────────────────────────────── */}
      <div style={{ marginBottom:11 }}>

        {/* Row 1: Tier + Correlation */}
        <div style={{ display:"flex", gap:5, flexWrap:"wrap", alignItems:"center", marginBottom:5 }}>
          <span style={{ fontSize:8, color:"#334155", marginRight:2 }}>TIER:</span>
          <Btn v="ALL"     cur={tierF} set={setTierF} />
          <Btn v="ELITE"   cur={tierF} set={setTierF} col="#22C55E" />
          <Btn v="STRONG"  cur={tierF} set={setTierF} col="#3B82F6" />
          <Btn v="PP LINK" cur={tierF} set={setTierF} col="#F59E0B" />
          <span style={{ fontSize:8, color:"#334155", margin:"0 2px 0 10px" }}>CORR:</span>
          <Btn v="ALL"       cur={corrF} set={setCorrF} />
          <Btn v="Strongest" cur={corrF} set={setCorrF} />
          <Btn v="High"      cur={corrF} set={setCorrF} />
          <Btn v="Moderate"  cur={corrF} set={setCorrF} />
          <Btn v="Lowest"    cur={corrF} set={setCorrF} />
        </div>

        {/* Row 2: Game */}
        <div style={{ display:"flex", gap:5, flexWrap:"wrap", alignItems:"center", marginBottom:5 }}>
          <span style={{ fontSize:8, color:"#334155", marginRight:2 }}>GAME:</span>
          <Btn v="ALL" cur={gameF} set={setGameF} />
          {GAME_ORDER.map(g => <Btn key={g} v={g} cur={gameF} set={setGameF} />)}
        </div>

        {/* Row 3: Team + search + bets toggle */}
        <div style={{ display:"flex", gap:5, flexWrap:"wrap", alignItems:"center" }}>
          <span style={{ fontSize:8, color:"#334155", marginRight:2 }}>TEAM:</span>
          <Btn v="ALL" cur={teamF} set={setTeamF} />
          {teams.map(t => <Btn key={t} v={t} cur={teamF} set={setTeamF} />)}
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search player…"
            style={{
              ...MONO, fontSize:10, background:"#0D1117",
              border:"1px solid #1E293B", color:"#E2E8F0",
              padding:"4px 9px", borderRadius:4, outline:"none",
              width:150, marginLeft:8,
            }}
          />
          <button
            onClick={() => setBets(v => !v)}
            style={{
              ...MONO, fontSize:8, fontWeight:700, padding:"4px 9px", borderRadius:4,
              cursor:"pointer", border:"1px solid",
              background: betsOnly ? "#120A00" : "transparent",
              borderColor: betsOnly ? "#92400E" : "#1E293B",
              color: betsOnly ? "#FCD34D" : "#475569",
              marginLeft:4,
            }}
          >
            ★ BETS ONLY{betsOnly ? " ✕" : ""}
          </button>
        </div>
      </div>

      {/* ── GAME BLOCKS ───────────────────────────────────────────────────── */}
      {GAME_ORDER_LIST.map(gid => {
        const info   = GAME_INFO[gid];
        const [aw, hw] = gid.split("@");
        const allG   = DUOS.filter(d => d.game === gid);
        const visG   = filtered.filter(d => d.game === gid);
        const isOpen = !collapsed[gid];
        const envC   = ENV_CFG[info.env] || ENV_CFG.MID;
        const topG   = allG.filter(d => d.top && !d.invalid && !d.cold);
        const recG   = REC.filter(d => d.game === gid);

        // Hide game block entirely when a filter is active and nothing matches
        if (hasFilter && gameF === "ALL" && visG.length === 0) return null;

        return (
          <div key={gid} style={{ border:"1px solid #1E293B", borderRadius:8, overflow:"hidden", marginBottom:10 }}>

            {/* ── Game header (clickable) ── */}
            <div
              onClick={() => toggleCol(gid)}
              style={{
                background:"#080C12",
                borderBottom: isOpen ? "1px solid #1E293B" : "none",
                padding:"10px 13px", cursor:"pointer",
                display:"flex", alignItems:"center", gap:10, flexWrap:"wrap",
              }}
            >
              {/* Matchup */}
              <span style={{ fontSize:17, fontWeight:900 }}>
                <span style={{ color: TEAM_COL[aw] || "#fff" }}>{aw}</span>
                <span style={{ color:"#1E293B", margin:"0 5px" }}>@</span>
                <span style={{ color: TEAM_COL[hw] || "#fff" }}>{hw}</span>
              </span>

              {/* Time */}
              <span style={{ fontSize:10, color:"#475569" }}>{info.time} ET</span>

              {/* ENV + O/U badge */}
              <span style={{
                fontSize:8, fontWeight:700, color:envC.tx,
                border:`1px solid ${envC.bd}`, padding:"2px 7px",
                borderRadius:3, background:"#0A0E18",
              }}>
                {info.env} · O/U {info.ou}
              </span>

              {/* Recommended target count */}
              {recG.length > 0 && (
                <span style={{
                  fontSize:8, fontWeight:700, color:"#4ADE80",
                  background:"#052E16", border:"1px solid #16A34A",
                  padding:"2px 7px", borderRadius:3,
                }}>
                  🎯 {recG.length} TARGET{recG.length > 1 ? "S" : ""}
                </span>
              )}

              {/* Game context */}
              <span style={{ fontSize:9, color:"#64748B", flex:1, minWidth:80 }}>{info.context}</span>

              {/* Tier counts + collapse arrow */}
              <div style={{ display:"flex", gap:4, marginLeft:"auto", alignItems:"center" }}>
                {["ELITE","STRONG","PP LINK"].map(t => {
                  const n  = allG.filter(d => d.tier === t && !d.cold && !d.invalid).length;
                  const tc = TIER_CFG[t];
                  return n > 0 ? (
                    <span key={t} style={{
                      fontSize:7, padding:"2px 6px",
                      background:tc.bg, border:`1px solid ${tc.bd}`,
                      borderRadius:3, color:tc.tx,
                    }}>
                      {n}
                    </span>
                  ) : null;
                })}
                <span style={{ fontSize:11, color:"#334155", marginLeft:4 }}>
                  {isOpen ? "▲" : "▼"}
                </span>
              </div>
            </div>

            {/* ── Expanded content ── */}
            {isOpen && (
              <div>

                {/* TOP plays strip */}
                {topG.length > 0 && (
                  <div style={{
                    background:"#050A08", borderBottom:"1px solid #1E293B",
                    padding:"6px 12px", display:"flex", gap:6, flexWrap:"wrap", alignItems:"center",
                  }}>
                    <span style={{ fontSize:8, color:"#334155", marginRight:2 }}>TOP:</span>
                    {topG.map(d => {
                      const on  = myBets.has(d.id);
                      const tc  = TIER_CFG[d.tier];
                      const ir  = REC.some(r => r.id === d.id);
                      return (
                        <div key={d.id} style={{
                          display:"flex", alignItems:"center", gap:5,
                          padding:"3px 9px", background: on ? "#1A0F00" : "#0D1117",
                          border:`1px solid ${ir ? "#16A34A" : on ? "#92400E" : tc.bd + "66"}`,
                          borderRadius:4,
                        }}>
                          {ir && <span style={{ fontSize:9, color:"#4ADE80" }}>🎯</span>}
                          <span style={{ fontSize:9, fontWeight:700, color: TEAM_COL[d.team] || "#fff" }}>{d.team}</span>
                          <span style={{ fontSize:10, fontWeight:700, color:"#F8FAFC" }}>{d.a}+{d.b}</span>
                          <TierBadge tier={d.tier} />
                          <CorrBadge corr={d.corr} />
                          <StarBtn on={on} toggle={() => toggleBet(d.id)} />
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Column headers */}
                <div style={{
                  display:"grid",
                  gridTemplateColumns:"30px 58px 1fr 1fr 88px 80px 96px 1fr",
                  background:"#040608", borderBottom:"1px solid #0A0E18", padding:"4px 10px",
                }}>
                  {["★","TEAM","PLAYER A","PLAYER B","TIER","CONN TYPE","CORR STRENGTH","NOTES"].map((h, i) => (
                    <div key={i} style={{ fontSize:7, color:"#1E3A5F", fontWeight:700 }}>{h}</div>
                  ))}
                </div>

                {/* Duo rows */}
                {(hasFilter ? visG : allG).map(d => <Row key={d.id} d={d} />)}

                {/* Empty state */}
                {hasFilter && visG.length === 0 && (
                  <div style={{ padding:"14px", textAlign:"center", fontSize:10, color:"#334155" }}>
                    No duos match current filters.
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {/* ── PRE-PUCK-DROP + SEASON STATS + COLD FLAGS ────────────────────── */}
      <div style={{ marginTop:14, background:"#080C12", border:"1px solid #1E293B", borderRadius:8, padding:"12px 14px" }}>

        {/* ── Pre-puck-drop refresh ── */}
        <div style={{ fontSize:12, fontWeight:900, color:"#FB923C", marginBottom:9 }}>
          🔁 PRE-PUCK-DROP REFRESH — Manual Verification Required Before 8:30 PM ET
        </div>
        {[
          ["🚑 MAKAR (COL)",       "CONFIRM OUT",   "Bednar said 'not serious, will miss some time' — but coaches sometimes clear players at warmups. Check ~1hr before puck drop. If Makar plays → Toews+MacKinnon PP LINK becomes INVALID (Makar resumes PP1 QB)."],
          ["⚠️ R.THOMAS (STL)",    "COLD FLAG",     "Thomas cold-flagged (2+ consecutive blanks). Check if STL confirms he's even in lineup tonight — if scratched, Thomas+Holloway ELITE is fully INVALID. His streak status determines all STL L1/PP1 plays."],
          ["⚠️ COL PP1 STRUCTURE", "TOEWS QB?",     "DFO dated Mar 28 — does not reflect Makar absence. Confirm via CHN/Colorado Hockey Now before puck drop that Toews (not Burns or Malinski) is indeed taking PP1 QB tonight."],
          ["⚠️ VAN EFFORT LEVEL",  "LOW MOTIVATION","VAN eliminated, last in NHL (50 pts). Verify VAN's lineup vs starting goalies report. If they're resting stars, all VAN duos drop in value significantly. Pettersson and Boeser may get nights off."],
          ["⚠️ STL LINEUP (STALE)","DFO Mar 23",    "STL DFO is 9 days stale. Check today's STL lines before playing any STL duo — Kyrou's return status unknown, and multiple line shuffles possible. Use Inside The Rink or STL beat reporter for confirmation."],
          ["✅ ANA (FRESH)",        "DFO Apr 1 TODAY","ANA DFO updated at 12:04 ET today. Freshest lines on the entire slate. J.Carlson→Carlsson PP1 chain confirmed. High confidence in ANA duos — lowest staleness risk."],
          ["✅ SJS (NEAR-FRESH)",   "DFO Mar 31",    "SJS DFO updated yesterday from last game. High confidence in Celebrini+W.Smith and Orlov→Celebrini chains. Confirm SJS starting goalie (Askarov vs Kahkonen) for game context."],
        ].map(([tag, status, obs], i) => {
          const statusColor =
            /OUT|COLD|STALE|LOW/.test(status)         ? "#FCA5A5" :
            /FRESH|NEAR/.test(status)                  ? "#4ADE80" :
            "#FCD34D";
          return (
            <div key={i} style={{
              display:"flex", gap:10, padding:"7px 9px",
              borderBottom:"1px solid #0A0E18",
              background: i % 2 === 0 ? "#080C12" : "#0D1117",
            }}>
              <span style={{ fontSize:8, fontWeight:700, color:"#F8FAFC", minWidth:130, flexShrink:0 }}>{tag}</span>
              <span style={{ fontSize:8, fontWeight:700, color:statusColor, minWidth:110, flexShrink:0 }}>{status}</span>
              <span style={{ fontSize:9.5, color:"#CBD5E1" }}>{obs}</span>
            </div>
          );
        })}

        {/* ── Season stats ── */}
        <div style={{ fontSize:12, fontWeight:900, color:"#FBBF24", marginBottom:9, marginTop:14 }}>
          📊 SEASON STATS — THRU MAR 31 2026
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(195px,1fr))", gap:8, marginBottom:10 }}>
          {[
            ...Object.entries(SEASON),
            ["TOTAL", Object.values(SEASON).reduce((a, s) => ({ W: a.W + s.W, L: a.L + s.L, CW: a.CW + s.CW }), { W:0, L:0, CW:0 })],
          ].map(([tier, s]) => {
            const tc  = TIER_CFG[tier] || { bg:"#0D1117", bd:"#1E293B", tx:"#94A3B8" };
            const pct = (s.W / (s.W + s.L) * 100).toFixed(1);
            const co  = s.W > 0 ? (s.CW / s.W * 100).toFixed(1) : "0.0";
            return (
              <div key={tier} style={{ background:tc.bg, border:`1px solid ${tc.bd}`, borderRadius:7, padding:"10px 12px" }}>
                <div style={{ fontSize:11, fontWeight:800, color:tc.tx, marginBottom:6 }}>{tier}</div>
                {/* Win % bar */}
                <div style={{ background:"#00000040", borderRadius:4, height:6, marginBottom:5, overflow:"hidden" }}>
                  <div style={{ background:tc.tx, height:6, width:`${pct}%`, borderRadius:4 }} />
                </div>
                <div style={{ fontSize:11, display:"flex", gap:8, marginBottom:3 }}>
                  <span style={{ color:"#4ADE80" }}>{s.W}W</span>
                  <span style={{ color:"#F87171" }}>{s.L}L</span>
                  <span style={{ color:tc.tx, fontWeight:800 }}>{pct}%</span>
                </div>
                <div style={{ fontSize:9, color:"#94A3B8" }}>
                  Chain OV: <span style={{ color:tc.tx, fontWeight:700 }}>{co}%</span>
                  <span style={{ color:"#475569" }}> ({s.CW}/{s.W}W)</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── Active cold flags ── */}
        <div style={{ fontSize:10, fontWeight:700, color:"#FBBF24", marginBottom:7 }}>
          ❄️ ACTIVE COLD FLAGS (Season Rolling)
        </div>
        {[
          ["🚑 INJURED", "Makar (C.)",    "COL", "OUT tonight — UBI. Confirm status ~1hr before puck drop."],
          ["❄️ COLD",    "R.Thomas",      "STL", "2+ consecutive blanks. All Thomas duos EXCLUDED until he scores."],
          ["❄️ COLD WATCH","D.Holloway",  "STL", "Thomas cold flag affects Holloway L1+PP1 duos indirectly."],
          ["🚑 INJURED", "Draisaitl",     "EDM", "LBI. Not on tonight's slate. Season dataset cold flag remains."],
          ["❄️ COLD",    "E.Karlsson",    "PIT", "2 consecutive blanks (Mar 30-31). Not tonight. Cold flag active."],
          ["❄️ COLD",    "Schaefer (M.)", "NYI", "2 consecutive blanks. Not tonight. Cold flag active."],
          ["❄️ COLD",    "Barzal",        "NYI", "2 consecutive blanks. Not tonight. Cold flag active."],
        ].map(([tag, player, team, note], i) => (
          <div key={i} style={{
            display:"flex", gap:10, padding:"6px 9px",
            borderBottom:"1px solid #0A0E18",
            background: i % 2 === 0 ? "#080C12" : "#0D1117",
          }}>
            <span style={{ fontSize:8, fontWeight:700, color: tag.includes("🚑") ? "#FCD34D" : "#FCA5A5", minWidth:100, flexShrink:0 }}>
              {tag}
            </span>
            <span style={{ fontSize:8, fontWeight:700, color:"#F8FAFC", minWidth:90, flexShrink:0 }}>{player}</span>
            <span style={{ fontSize:8, color:"#475569", minWidth:36, flexShrink:0 }}>{team}</span>
            <span style={{ fontSize:9.5, color:"#CBD5E1" }}>{note}</span>
          </div>
        ))}

        {/* ── Footer ── */}
        <div style={{ marginTop:10, fontSize:8, color:"#1E293B", textAlign:"center" }}>
          Apr 1 2026 · Lines: Daily Faceoff (fetched {FETCH_TIME}) · Andy Frances methodology · For entertainment only
        </div>
      </div>

    </div>
  );
}
