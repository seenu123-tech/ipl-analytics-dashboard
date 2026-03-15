import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import warnings
from functools import lru_cache

warnings.filterwarnings("ignore")

st.set_page_config(page_title="IPL Analytics Pro", page_icon="🏏", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

API_BASE_URL = "http://127.0.0.1:8000"
FALLBACK_TO_CSV = True

TEAM_LOGOS = {
    "Mumbai Indians":              "https://upload.wikimedia.org/wikipedia/en/c/cd/Mumbai_Indians_Logo.svg",
    "Chennai Super Kings":         "https://upload.wikimedia.org/wikipedia/en/2/2b/Chennai_Super_Kings_Logo.svg",
    "Kolkata Knight Riders":       "https://upload.wikimedia.org/wikipedia/en/4/4c/Kolkata_Knight_Riders_Logo.svg",
    "Royal Challengers Bangalore": "https://upload.wikimedia.org/wikipedia/en/2/2a/Royal_Challengers_Bangalore_2020.svg",
    "Royal Challengers Bengaluru": "https://upload.wikimedia.org/wikipedia/en/2/2a/Royal_Challengers_Bangalore_2020.svg",
    "Sunrisers Hyderabad":         "https://upload.wikimedia.org/wikipedia/en/3/3b/Sunrisers_Hyderabad.png",
    "Rajasthan Royals":            "https://upload.wikimedia.org/wikipedia/en/6/60/Rajasthan_Royals_Logo.svg",
    "Delhi Capitals":              "https://upload.wikimedia.org/wikipedia/en/f/f5/Delhi_Capitals_Logo.svg",
    "Delhi Daredevils":            "https://upload.wikimedia.org/wikipedia/en/f/f5/Delhi_Capitals_Logo.svg",
    "Kings XI Punjab":             "https://upload.wikimedia.org/wikipedia/en/d/d4/Punjab_Kings_Logo.svg",
    "Punjab Kings":                "https://upload.wikimedia.org/wikipedia/en/d/d4/Punjab_Kings_Logo.svg",
    "Gujarat Titans":              "https://upload.wikimedia.org/wikipedia/en/0/09/Gujarat_Titans_Logo.svg",
    "Lucknow Super Giants":        "https://upload.wikimedia.org/wikipedia/en/b/bd/Lucknow_Super_Giants_Logo.svg",
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Nunito:wght@400;600;700&display=swap');
* { font-family:'Nunito',sans-serif; }
h1,h2,h3 { font-family:'Rajdhani',sans-serif !important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#04080f 0%,#0d1f3c 50%,#071526 100%) !important; border-right:2px solid #f0a500; }
[data-testid="stSidebar"] * { color:#ffffff !important; }
[data-testid="stSidebar"] .stSelectbox label,[data-testid="stSidebar"] .stRadio > label { color:#f0a500 !important; font-size:12px !important; font-weight:700 !important; letter-spacing:1px; text-transform:uppercase; }
[data-testid="stSidebar"] .stSelectbox > div > div { background-color:#0d1f3c !important; color:#ffffff !important; border:1px solid #f0a500 !important; border-radius:8px !important; }
[data-testid="stSidebar"] .stRadio > div { background:rgba(240,165,0,0.04); border-radius:10px; padding:6px; border:1px solid rgba(240,165,0,0.1); }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p { color:#ffffff !important; font-size:13px !important; }
.stApp { background:#05101e; }
.section-header { font-family:'Rajdhani',sans-serif; font-size:24px; font-weight:700; color:#f0a500; margin:20px 0 12px; padding-bottom:8px; border-bottom:2px solid rgba(240,165,0,0.35); letter-spacing:1px; }
[data-testid="stMetric"] { background:linear-gradient(135deg,#0d1f3c,#071526); border:1px solid rgba(240,165,0,0.25); border-radius:14px; padding:14px !important; }
[data-testid="stMetricValue"] { color:#f0a500 !important; }
.kpi-banner { display:flex; gap:14px; margin:0 0 20px 0; flex-wrap:wrap; }
.kpi-card { flex:1; min-width:150px; border-radius:16px; padding:18px 12px; text-align:center; transition:transform 0.2s ease; }
.kpi-card:hover { transform:translateY(-4px); }
.kpi-card-gold  { background:linear-gradient(135deg,#f0a500,#b37400); border:1px solid rgba(255,200,50,0.3); box-shadow:0 6px 30px rgba(240,165,0,0.3); }
.kpi-card-orange{ background:linear-gradient(135deg,#e85d04,#9d0208); border:1px solid rgba(255,100,0,0.3); box-shadow:0 6px 30px rgba(232,93,4,0.3); }
.kpi-card-purple{ background:linear-gradient(135deg,#7209b7,#3a0ca3); border:1px solid rgba(150,50,255,0.3); box-shadow:0 6px 30px rgba(114,9,183,0.3); }
.kpi-card-blue  { background:linear-gradient(135deg,#0077b6,#023e8a); border:1px solid rgba(0,150,255,0.3); box-shadow:0 6px 30px rgba(0,119,182,0.3); }
.kpi-card-green { background:linear-gradient(135deg,#2dc653,#1a7431); border:1px solid rgba(50,200,100,0.3); box-shadow:0 6px 30px rgba(45,198,83,0.3); }
.kpi-icon { font-size:28px; margin-bottom:6px; }
.kpi-label { font-size:9px; font-weight:700; letter-spacing:2px; color:rgba(255,255,255,0.7); text-transform:uppercase; margin-bottom:4px; }
.kpi-name { font-family:'Rajdhani',sans-serif; font-size:15px; font-weight:700; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.kpi-value { font-family:'Rajdhani',sans-serif; font-size:28px; font-weight:700; color:#fff; }
.kpi-sub { font-size:10px; color:rgba(255,255,255,0.6); margin-top:2px; }
.season-title { text-align:center; font-family:'Rajdhani',sans-serif; font-size:14px; font-weight:700; color:#f0a500; letter-spacing:3px; text-transform:uppercase; margin-bottom:12px; padding:10px; background:linear-gradient(90deg,rgba(240,165,0,0.03),rgba(240,165,0,0.1),rgba(240,165,0,0.03)); border-radius:10px; border:1px solid rgba(240,165,0,0.2); }
.winner-grid { display:flex; flex-wrap:wrap; gap:12px; margin:10px 0 24px; }
.winner-card { flex:1; min-width:150px; max-width:190px; background:linear-gradient(135deg,#0d1f3c,#071526); border:1px solid rgba(240,165,0,0.2); border-radius:14px; padding:14px 10px; text-align:center; transition:all 0.2s ease; }
.winner-card:hover { border-color:#f0a500; box-shadow:0 6px 24px rgba(240,165,0,0.2); transform:translateY(-3px); }
.season-badge { font-family:'Rajdhani',sans-serif; font-size:11px; font-weight:700; letter-spacing:2px; color:#f0a500; text-transform:uppercase; margin-bottom:8px; }
.team-logo-wrap { width:56px; height:56px; margin:0 auto 8px; background:rgba(255,255,255,0.05); border-radius:50%; display:flex; align-items:center; justify-content:center; border:1px solid rgba(255,255,255,0.1); overflow:hidden; }
.team-logo-wrap img { width:46px; height:46px; object-fit:contain; }
.team-name-label { font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:700; color:#fff; line-height:1.3; }
.player-profile { background:linear-gradient(135deg,#0d1f3c,#071526); border:1px solid rgba(240,165,0,0.4); border-radius:20px; padding:28px; margin:16px 0; display:flex; gap:28px; flex-wrap:wrap; align-items:flex-start; }
.player-img-wrap { width:110px; height:110px; border-radius:50%; overflow:hidden; border:3px solid #f0a500; background:#0d1f3c; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:48px; }
.player-img-wrap img { width:100%; height:100%; object-fit:cover; }
.player-name { font-family:'Rajdhani',sans-serif; font-size:32px; font-weight:700; color:#f0a500; margin:0 0 4px; }
.player-subtitle { font-size:12px; color:rgba(255,255,255,0.45); margin-bottom:16px; letter-spacing:1px; text-transform:uppercase; }
.stats-row { display:flex; flex-wrap:wrap; gap:16px; }
.stat-box { text-align:center; min-width:65px; }
.stat-box-val { font-family:'Rajdhani',sans-serif; font-size:24px; font-weight:700; }
.stat-box-lbl { font-size:9px; color:rgba(255,255,255,0.45); letter-spacing:1px; text-transform:uppercase; margin-top:2px; }
.cricket-banner { background:linear-gradient(135deg,#f0a500,#e07b00); border-radius:10px; padding:9px; text-align:center; margin:8px 0; color:#04080f !important; font-weight:700; font-size:11px; letter-spacing:2px; text-transform:uppercase; }
.stat-strip { display:flex; justify-content:space-around; background:rgba(240,165,0,0.05); border:1px solid rgba(240,165,0,0.15); border-radius:10px; padding:10px 4px; margin:8px 0; }
.stat-num { font-family:'Rajdhani',sans-serif; font-size:20px; font-weight:700; color:#f0a500 !important; display:block; }
.stat-lbl { font-size:9px; color:rgba(255,255,255,0.5) !important; display:block; letter-spacing:1px; text-transform:uppercase; }
.match-card { background:linear-gradient(135deg,#0d1f3c,#071526); border:1px solid #f0a500; border-radius:14px; padding:18px; margin:12px 0; }
</style>
""", unsafe_allow_html=True)

HOVER = dict(bgcolor="#0d1f3c", font_size=13, font_color="white", bordercolor="#f0a500")

# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING - FIXED: Load before sidebar!
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_data():
    """Load data from CSV files"""
    try:
        matches = pd.read_csv("data/matches.csv")
        deliveries = pd.read_csv("data/deliveries.csv")
        return matches, deliveries
    except Exception as e:
        st.error(f"Error loading CSV files: {e}")
        return None, None

# Load data BEFORE sidebar
matches, deliveries = load_data()

if matches is None or deliveries is None:
    st.error("Failed to load data. Please check your CSV files.")
    st.stop()

# Handle column variations
batter_col    = 'batter'         if 'batter'         in deliveries.columns else 'batsman'
runs_col      = 'batsman_runs'   if 'batsman_runs'    in deliveries.columns else 'batter_runs'
dismissal_col = 'dismissal_kind' if 'dismissal_kind'  in deliveries.columns else 'player_dismissed'

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR - Now can use matches safely
# ═══════════════════════════════════════════════════════════════════════════

st.sidebar.markdown("""
<div style="text-align:center;padding:14px 0 8px;">
    <div style="font-size:44px;">🏆</div>
    <div style="font-family:'Rajdhani',sans-serif;color:#f0a500;font-size:22px;font-weight:700;letter-spacing:3px;margin-top:4px;">IPL PRO</div>
    <div style="color:rgba(255,255,255,0.3);font-size:9px;letter-spacing:4px;margin-top:2px;">ANALYTICS DASHBOARD</div>
</div>""", unsafe_allow_html=True)

st.sidebar.markdown('<div class="cricket-banner">🏏 IPL Analytics Dashboard</div>', unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="display:flex;gap:6px;margin:8px 0 6px;">
    <div style="flex:1;background:linear-gradient(135deg,#0d1f3c,#071526);border:1px solid rgba(240,165,0,0.2);border-radius:9px;padding:10px 4px;text-align:center;"><div style="font-size:20px;">🏏</div><div style="color:#f0a500!important;font-size:8px;font-weight:700;margin-top:3px;letter-spacing:1px;">BAT</div></div>
    <div style="flex:1;background:linear-gradient(135deg,#0d1f3c,#071526);border:1px solid rgba(240,165,0,0.2);border-radius:9px;padding:10px 4px;text-align:center;"><div style="font-size:20px;">🎳</div><div style="color:#f0a500!important;font-size:8px;font-weight:700;margin-top:3px;letter-spacing:1px;">BOWL</div></div>
    <div style="flex:1;background:linear-gradient(135deg,#0d1f3c,#071526);border:1px solid rgba(240,165,0,0.2);border-radius:9px;padding:10px 4px;text-align:center;"><div style="font-size:20px;">🏆</div><div style="color:#f0a500!important;font-size:8px;font-weight:700;margin-top:3px;letter-spacing:1px;">WIN</div></div>
    <div style="flex:1;background:linear-gradient(135deg,#0d1f3c,#071526);border:1px solid rgba(240,165,0,0.2);border-radius:9px;padding:10px 4px;text-align:center;"><div style="font-size:20px;">🏟️</div><div style="color:#f0a500!important;font-size:8px;font-weight:700;margin-top:3px;letter-spacing:1px;">VEN</div></div>
</div>""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div class="stat-strip">
    <div><span class="stat-num">16</span><span class="stat-lbl">Seasons</span></div>
    <div><span class="stat-num">10</span><span class="stat-lbl">Teams</span></div>
    <div><span class="stat-num">950+</span><span class="stat-lbl">Matches</span></div>
</div>""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Filters
seasons = sorted(matches['season'].astype(str).unique())
selected_season = st.sidebar.selectbox("📅 Season", ["All"] + list(seasons))

teams = sorted(matches['team1'].unique())
selected_team = st.sidebar.selectbox("🏏 Team", ["All"] + list(teams))

st.sidebar.markdown("---")

page = st.sidebar.radio("📌 Navigate", [
    "🏠 Overview",
    "🏆 Season Winners",
    "🎯 Batting Stats",
    "🎳 Bowling Stats",
    "📍 Venue Analysis",
    "🪙 Toss Analysis",
    "🔍 Player Profile",
    "⚔️ Player Comparison",
    "📈 Match Analysis",
    "🤖 Win Predictor",
    "📤 Export Data"
])

st.sidebar.markdown("""<div style="text-align:center;margin-top:16px;color:rgba(255,255,255,0.2)!important;font-size:9px;letter-spacing:1px;">IPL 2008–2024 · Streamlit 🏏</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# DATA FILTERING
# ═══════════════════════════════════════════════════════════════════════════

filtered_matches = matches.copy()
if selected_season != "All":
    filtered_matches = filtered_matches[filtered_matches['season'].astype(str)==selected_season]
if selected_team != "All":
    filtered_matches = filtered_matches[(filtered_matches['team1']==selected_team)|(filtered_matches['team2']==selected_team)]

if len(filtered_matches)==0:
    st.warning("⚠️ No matches found.")
    st.stop()

filtered_delivery_ids = filtered_matches['id'].unique()
filtered_deliveries   = deliveries[deliveries['match_id'].isin(filtered_delivery_ids)]

# ═══════════════════════════════════════════════════════════════════════════
# KPI CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data
def get_season_kpis(season_str, _matches, _deliveries, bc, rc, dc):
    try:
        m = _matches if season_str == "All" else _matches[_matches['season'].astype(str) == season_str]
        if len(m) == 0: return None
        d = _deliveries[_deliveries['match_id'].isin(m['id'].unique())]
        wc = m['winner'].value_counts()
        winner = wc.idxmax() if len(wc)>0 else "N/A"
        wins   = int(wc.max()) if len(wc)>0 else 0
        bat = d.groupby(bc)[rc].sum()
        orange_cap  = bat.idxmax()  if len(bat)>0 else "N/A"
        orange_runs = int(bat.max()) if len(bat)>0 else 0
        bowl = d[d[dc].notna()].groupby('bowler')[dc].count()
        purple_cap     = bowl.idxmax()  if len(bowl)>0 else "N/A"
        purple_wickets = int(bowl.max()) if len(bowl)>0 else 0
        mb = d.groupby(['match_id',bc])[rc].sum()
        top_scorer    = mb.idxmax()[1] if len(mb)>0 else "N/A"
        highest_score = int(mb.max())  if len(mb)>0 else 0
        mbow = d[d[dc].notna()].groupby(['match_id','bowler'])[dc].count()
        best_bowler    = mbow.idxmax()[1] if len(mbow)>0 else "N/A"
        best_bowl_wkts = int(mbow.max())  if len(mbow)>0 else 0
        return dict(winner=winner, wins=wins, orange_cap=orange_cap, orange_runs=orange_runs,
                    purple_cap=purple_cap, purple_wickets=purple_wickets,
                    top_scorer=top_scorer, highest_score=highest_score,
                    best_bowler=best_bowler, best_bowl_wkts=best_bowl_wkts,
                    total_runs=int(d[rc].sum()), total_sixes=int((d[rc]==6).sum()),
                    total_fours=int((d[rc]==4).sum()))
    except Exception as e:
        st.warning(f"Error calculating KPIs: {e}")
        return None

@st.cache_data
def get_all_season_winners(_matches):
    rows = []
    for s in sorted(_matches['season'].unique()):
        sm = _matches[_matches['season']==s]
        wc = sm['winner'].value_counts()
        if len(wc)>0: rows.append({"season":str(s),"winner":wc.idxmax(),"wins":int(wc.max())})
    return rows

# ═══════════════════════════════════════════════════════════════════════════
# KPI BANNER
# ═══════════════════════════════════════════════════════════════════════════

kpis  = get_season_kpis(selected_season, matches, deliveries, batter_col, runs_col, dismissal_col)
label = f"Season {selected_season}" if selected_season != "All" else "All Seasons"

if kpis:
    # FIXED: Team logo with proper error handling
    wlogo = TEAM_LOGOS.get(kpis['winner'],"")
    logo_html = (f'<img src="{wlogo}" style="width:32px;height:32px;object-fit:contain;vertical-align:middle;" alt="{kpis["winner"]}" onerror="this.style.display=\'none\'" />' if wlogo else "🏆")
    
    st.markdown(f'<div class="season-title">🏏 {label} — Season Highlights</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="kpi-banner">
  <div class="kpi-card kpi-card-gold"><div class="kpi-icon">{logo_html}</div><div class="kpi-label">Champion</div><div class="kpi-name">{kpis['winner']}</div><div class="kpi-value">{kpis['wins']}</div><div class="kpi-sub">wins</div></div>
  <div class="kpi-card kpi-card-orange"><div class="kpi-icon">🟠</div><div class="kpi-label">Orange Cap</div><div class="kpi-name">{kpis['orange_cap']}</div><div class="kpi-value">{kpis['orange_runs']}</div><div class="kpi-sub">runs</div></div>
  <div class="kpi-card kpi-card-purple"><div class="kpi-icon">🟣</div><div class="kpi-label">Purple Cap</div><div class="kpi-name">{kpis['purple_cap']}</div><div class="kpi-value">{kpis['purple_wickets']}</div><div class="kpi-sub">wickets</div></div>
  <div class="kpi-card kpi-card-blue"><div class="kpi-icon">🏏</div><div class="kpi-label">Highest Score</div><div class="kpi-name">{kpis['top_scorer']}</div><div class="kpi-value">{kpis['highest_score']}</div><div class="kpi-sub">runs in a match</div></div>
  <div class="kpi-card kpi-card-green"><div class="kpi-icon">🎳</div><div class="kpi-label">Best Bowling</div><div class="kpi-name">{kpis['best_bowler']}</div><div class="kpi-value">{kpis['best_bowl_wkts']}</div><div class="kpi-sub">wickets in a match</div></div>
</div>""", unsafe_allow_html=True)
    
    st.markdown(f"""
<div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
  <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#0d1f3c,#071526);border:1px solid rgba(240,165,0,0.15);border-radius:12px;padding:12px;text-align:center;"><div style="font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;color:#f0a500;">{kpis['total_runs']:,}</div><div style="font-size:9px;color:rgba(255,255,255,0.4);letter-spacing:1px;text-transform:uppercase;">Total Runs</div></div>
  <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#0d1f3c,#071526);border:1px solid rgba(240,165,0,0.15);border-radius:12px;padding:12px;text-align:center;"><div style="font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;color:#e85d04;">{kpis['total_sixes']:,}</div><div style="font-size:9px;color:rgba(255,255,255,0.4);letter-spacing:1px;text-transform:uppercase;">Total Sixes</div></div>
  <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#0d1f3c,#071526);border:1px solid rgba(240,165,0,0.15);border-radius:12px;padding:12px;text-align:center;"><div style="font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;color:#2dc653;">{kpis['total_fours']:,}</div><div style="font-size:9px;color:rgba(255,255,255,0.4);letter-spacing:1px;text-transform:uppercase;">Total Fours</div></div>
  <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#0d1f3c,#071526);border:1px solid rgba(240,165,0,0.15);border-radius:12px;padding:12px;text-align:center;"><div style="font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;color:#7209b7;">{len(filtered_matches)}</div><div style="font-size:9px;color:rgba(255,255,255,0.4);letter-spacing:1px;text-transform:uppercase;">Matches</div></div>
</div>""", unsafe_allow_html=True)
    st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def styled_bar(df, x, y, color_col, scale, hover_tpl, orient='h'):
    try:
        fig = px.bar(df, x=x, y=y, orientation=orient, color=color_col, color_continuous_scale=scale)
        fig.update_traces(hovertemplate=hover_tpl,
                          selected=dict(marker=dict(color='#f0a500',opacity=1.0)),
                          unselected=dict(marker=dict(opacity=0.35)),
                          selector=dict(type='bar'))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          hoverlabel=HOVER, hovermode='closest', clickmode='event+select', dragmode='select',
                          font=dict(color='white'),
                          yaxis={'categoryorder':'total ascending','gridcolor':'rgba(255,255,255,0.04)'} if orient=='h' else {'gridcolor':'rgba(255,255,255,0.04)'},
                          xaxis={'gridcolor':'rgba(255,255,255,0.04)'})
        return fig
    except Exception as e:
        st.error(f"Error creating chart: {e}")
        return None

def pltcfg(fig):
    if fig is None:
        return None
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                      font=dict(color='white'),
                      xaxis=dict(gridcolor='rgba(255,255,255,0.04)'),
                      yaxis=dict(gridcolor='rgba(255,255,255,0.04)'))
    return fig

# ═══════════════════════════════════════════════════════════════════════════
# PAGES
# ═══════════════════════════════════════════════════════════════════════════

if page == "🏠 Overview":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">🏏 IPL Overview</h1>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🏟️ Matches", len(filtered_matches))
    c2.metric("📅 Seasons", filtered_matches['season'].nunique())
    c3.metric("🏆 Teams",   pd.unique(filtered_matches[['team1','team2']].values.ravel()).shape[0])
    c4.metric("👑 Most Wins", filtered_matches['winner'].value_counts().idxmax())
    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">Matches Per Season</div>', unsafe_allow_html=True)
        sc = matches.groupby('season').size().reset_index(name='Matches')
        fig = px.bar(sc, x='season', y='Matches', color='Matches', color_continuous_scale='Blues')
        fig.update_traces(hovertemplate="<b>Season %{x}</b><br>Matches: %{y}<extra></extra>",
                          selected=dict(marker=dict(color='#f0a500')),unselected=dict(marker=dict(opacity=0.35)))
        pltcfg(fig).update_layout(hoverlabel=HOVER,hovermode='x unified',clickmode='event+select')
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown('<div class="section-header">Top 10 Teams by Wins</div>', unsafe_allow_html=True)
        wc = filtered_matches['winner'].value_counts().head(10).reset_index(); wc.columns=['Team','Wins']
        fig = styled_bar(wc,'Wins','Team','Wins','Oranges',"<b>%{y}</b><br>🏆 Wins: %{x}<extra></extra>")
        if fig: st.plotly_chart(fig, use_container_width=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">Win Method</div>', unsafe_allow_html=True)
        wt = filtered_matches['result'].value_counts().reset_index(); wt.columns=['Result','Count']
        fig = px.pie(wt, names='Result', values='Count', hole=0.45, color_discrete_sequence=['#f0a500','#e85d04','#7209b7','#0077b6'])
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",pull=[0.04]*len(wt))
        fig.update_layout(hoverlabel=HOVER,paper_bgcolor='rgba(0,0,0,0)',font=dict(color='white'))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown('<div class="section-header">Player of the Match — Top 10</div>', unsafe_allow_html=True)
        potm = filtered_matches['player_of_match'].value_counts().head(10).reset_index(); potm.columns=['Player','Awards']
        fig = styled_bar(potm,'Awards','Player','Awards','Teal',"<b>%{y}</b><br>🥇 Awards: %{x}<extra></extra>")
        if fig: st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="section-header">Season Win Trend — Top 5 Teams</div>', unsafe_allow_html=True)
    top5  = matches['winner'].value_counts().head(5).index.tolist()
    trend = matches[matches['winner'].isin(top5)].groupby(['season','winner']).size().reset_index(name='wins')
    fig   = px.line(trend, x='season', y='wins', color='winner', markers=True, color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Season %{x}: %{y} wins<extra></extra>",line=dict(width=2.5),marker=dict(size=8))
    pltcfg(fig).update_layout(hoverlabel=HOVER,hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

elif page == "🏆 Season Winners":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">🏆 IPL Season Champions</h1>', unsafe_allow_html=True)
    season_winners = get_all_season_winners(matches)
    cards_html = '<div class="winner-grid">'
    for sw in season_winners:
        logo  = TEAM_LOGOS.get(sw['winner'],"")
        lhtml = f'<img src="{logo}" onerror="this.style.display=\'none\'" alt="{sw["winner"]}">' if logo else "🏆"
        cards_html += f'<div class="winner-card"><div class="season-badge">IPL {sw["season"]}</div><div class="team-logo-wrap">{lhtml}</div><div class="team-name-label">{sw["winner"]}</div><div style="font-size:16px;margin-top:6px;">🏆</div></div>'
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="section-header">All-time IPL Titles</div>', unsafe_allow_html=True)
    tc = {}
    for sw in season_winners: tc[sw['winner']] = tc.get(sw['winner'],0)+1
    tc_df = pd.DataFrame(list(tc.items()),columns=['Team','Titles']).sort_values('Titles',ascending=False)
    fig = styled_bar(tc_df,'Titles','Team','Titles','YlOrRd',"<b>%{y}</b><br>🏆 Titles: %{x}<extra></extra>")
    if fig: st.plotly_chart(fig, use_container_width=True)

elif page == "🎯 Batting Stats":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">🎯 Batting Statistics</h1>', unsafe_allow_html=True)
    batting = filtered_deliveries.groupby(batter_col).agg(Runs=(runs_col,'sum'),Balls=('ball','count'),Fours=(runs_col,lambda x:(x==4).sum()),Sixes=(runs_col,lambda x:(x==6).sum())).reset_index()
    batting.rename(columns={batter_col:'batsman'},inplace=True)
    batting['Strike_Rate'] = (batting['Runs']/batting['Balls']*100).round(2)
    batting = batting.sort_values('Runs',ascending=False)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">Top 10 Run Scorers</div>', unsafe_allow_html=True)
        fig = styled_bar(batting.head(10),'Runs','batsman','Strike_Rate','RdYlGn',"<b>%{y}</b><br>🏏 Runs: %{x}<extra></extra>")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown('<div class="section-header">Top 10 Six Hitters</div>', unsafe_allow_html=True)
        fig = styled_bar(batting.nlargest(10,'Sixes')[['batsman','Sixes']],'Sixes','batsman','Sixes','Purples',"<b>%{y}</b><br>6️⃣ Sixes: %{x}<extra></extra>")
        if fig: st.plotly_chart(fig, use_container_width=True)
    st.dataframe(batting.head(30), use_container_width=True, hide_index=True)

elif page == "🎳 Bowling Stats":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">🎳 Bowling Statistics</h1>', unsafe_allow_html=True)
    bowling = filtered_deliveries[filtered_deliveries[dismissal_col].notna()].groupby('bowler').agg(Wickets=(dismissal_col,'count'),Runs_Given=('total_runs','sum'),Balls=('ball','count')).reset_index()
    bowling['Economy'] = (bowling['Runs_Given']/(bowling['Balls']/6)).round(2)
    bowling = bowling[bowling['Wickets']>=10].sort_values('Wickets',ascending=False)
    if len(bowling)==0:
        st.info("⚠️ Not enough data. Try 'All' seasons.")
    else:
        c1,c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-header">Top 10 Wicket Takers</div>', unsafe_allow_html=True)
            fig = styled_bar(bowling.head(10),'Wickets','bowler','Economy','RdYlGn_r',"<b>%{y}</b><br>🎳 Wickets: %{x}<extra></extra>")
            if fig: st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown('<div class="section-header">Best Economy Rates</div>', unsafe_allow_html=True)
            fig = styled_bar(bowling.nsmallest(10,'Economy')[['bowler','Economy']],'Economy','bowler','Economy','Blues_r',"<b>%{y}</b><br>💰 Economy: %{x:.2f}<extra></extra>")
            if fig: st.plotly_chart(fig, use_container_width=True)
        st.dataframe(bowling.head(30), use_container_width=True, hide_index=True)

elif page == "📍 Venue Analysis":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">📍 Venue Analysis</h1>', unsafe_allow_html=True)
    vc = filtered_matches['venue'].value_counts().head(10).reset_index(); vc.columns=['Venue','Matches']
    st.markdown('<div class="section-header">Top 10 Venues</div>', unsafe_allow_html=True)
    fig = styled_bar(vc,'Matches','Venue','Matches','Mint',"<b>%{y}</b><br>🏟️ Matches: %{x}<extra></extra>")
    if fig: st.plotly_chart(fig, use_container_width=True)

elif page == "🪙 Toss Analysis":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">🪙 Toss Analysis</h1>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">Toss Decision</div>', unsafe_allow_html=True)
        td = filtered_matches['toss_decision'].value_counts().reset_index(); td.columns=['Decision','Count']
        fig = px.pie(td,names='Decision',values='Count',hole=0.45,color_discrete_sequence=['#0077b6','#f0a500'])
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",pull=[0.05,0.05])
        fig.update_layout(hoverlabel=HOVER,paper_bgcolor='rgba(0,0,0,0)',font=dict(color='white'))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown('<div class="section-header">Toss → Match Winner?</div>', unsafe_allow_html=True)
        filtered_matches['tmw'] = filtered_matches['toss_winner']==filtered_matches['winner']
        tw = filtered_matches['tmw'].value_counts().reset_index(); tw.columns=['Won','Count']; tw['Won']=tw['Won'].map({True:'Yes',False:'No'})
        fig = px.pie(tw,names='Won',values='Count',hole=0.45,color_discrete_sequence=['#2dc653','#e85d04'])
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",pull=[0.05,0.05])
        fig.update_layout(hoverlabel=HOVER,paper_bgcolor='rgba(0,0,0,0)',font=dict(color='white'))
        st.plotly_chart(fig, use_container_width=True)

elif page == "🔍 Player Profile":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">🔍 Player Profile</h1>', unsafe_allow_html=True)
    all_players = sorted(deliveries[batter_col].dropna().unique().tolist())
    search_name = st.selectbox("🔎 Search Player", ["Select a player..."] + all_players)
    if search_name != "Select a player...":
        p_bat  = deliveries[deliveries[batter_col]==search_name]
        if len(p_bat) == 0:
            st.warning(f"No data found for {search_name}")
        else:
            total_runs  = int(p_bat[runs_col].sum())
            total_balls = int(len(p_bat))
            total_fours = int((p_bat[runs_col]==4).sum())
            total_sixes = int((p_bat[runs_col]==6).sum())
            strike_rate = round(total_runs/total_balls*100,2) if total_balls>0 else 0
            st.markdown(f"""
<div class="player-profile">
  <div class="player-img-wrap">🏏</div>
  <div style="flex:1;min-width:200px;">
    <div class="player-name">{search_name}</div>
    <div class="player-subtitle">IPL Career Statistics</div>
    <div class="stats-row">
      <div class="stat-box"><div class="stat-box-val" style="color:#f0a500;">{total_runs:,}</div><div class="stat-box-lbl">Runs</div></div>
      <div class="stat-box"><div class="stat-box-val" style="color:#f0a500;">{total_balls:,}</div><div class="stat-box-lbl">Balls</div></div>
      <div class="stat-box"><div class="stat-box-val" style="color:#e8c547;">{strike_rate}</div><div class="stat-box-lbl">Strike Rate</div></div>
      <div class="stat-box"><div class="stat-box-val" style="color:#2dc653;">{total_fours}</div><div class="stat-box-lbl">Fours</div></div>
      <div class="stat-box"><div class="stat-box-val" style="color:#e85d04;">{total_sixes}</div><div class="stat-box-lbl">Sixes</div></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

elif page == "⚔️ Player Comparison":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">⚔️ Player vs Player Comparison</h1>', unsafe_allow_html=True)
    players = sorted(deliveries[batter_col].dropna().unique())
    col1, col2 = st.columns(2)
    with col1:
        player1 = st.selectbox("Select Player 1", players, key="p1")
    with col2:
        player2 = st.selectbox("Select Player 2", [p for p in players if p != player1], key="p2")
    
    if player1 and player2:
        p1 = deliveries[deliveries[batter_col] == player1]
        p2 = deliveries[deliveries[batter_col] == player2]
        stats = pd.DataFrame({
            "Player":[player1,player2],
            "Runs":[p1[runs_col].sum(),p2[runs_col].sum()],
            "Balls":[len(p1),len(p2)],
            "Fours":[(p1[runs_col]==4).sum(),(p2[runs_col]==4).sum()],
            "Sixes":[(p1[runs_col]==6).sum(),(p2[runs_col]==6).sum()],
        })
        stats["Strike Rate"] = (stats["Runs"]/stats["Balls"]*100).round(2)
        st.dataframe(stats,use_container_width=True,hide_index=True)
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("### Runs Comparison")
            fig = px.bar(stats, x="Player", y="Runs", color="Player", color_discrete_sequence=['#0077b6','#f0a500'])
            pltcfg(fig)
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            st.markdown("### Strike Rate Comparison")
            fig = px.bar(stats, x="Player", y="Strike Rate", color="Player", color_discrete_sequence=['#0077b6','#f0a500'])
            pltcfg(fig)
            st.plotly_chart(fig,use_container_width=True)

elif page == "📈 Match Analysis":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">📈 Match Analysis</h1>', unsafe_allow_html=True)
    sl = sorted(matches['season'].astype(str).unique(),reverse=True)
    sels = st.selectbox("Select Season", sl)
    sm = matches[matches['season'].astype(str)==sels]
    opts = sm.apply(lambda r:f"{r['id']} | {r['team1']} vs {r['team2']}",axis=1).tolist()
    if opts:
        sel_m = st.selectbox("Select Match", opts)
        mid   = int(sel_m.split('|')[0].strip())
        minfo = matches[matches['id']==mid].iloc[0]
        mdel  = deliveries[deliveries['match_id']==mid]
        
        # FIXED: Logo with error handling
        t1l = TEAM_LOGOS.get(minfo['team1'],"")
        t2l = TEAM_LOGOS.get(minfo['team2'],"")
        t1h = f'<img src="{t1l}" style="width:28px;height:28px;object-fit:contain;vertical-align:middle;margin-right:4px;" alt="{minfo["team1"]}" onerror="this.style.display=\'none\'" />' if t1l else ""
        t2h = f'<img src="{t2l}" style="width:28px;height:28px;object-fit:contain;vertical-align:middle;margin-right:4px;" alt="{minfo["team2"]}" onerror="this.style.display=\'none\'" />' if t2l else ""
        
        st.markdown(f"""
<div class="match-card">
  <h3 style="font-family:'Rajdhani',sans-serif;color:#f0a500;margin:0;">{t1h}{minfo['team1']} <span style="color:rgba(255,255,255,0.25);">vs</span> {t2h}{minfo['team2']}</h3>
  <p style="color:rgba(255,255,255,0.5);margin:6px 0 0;font-size:13px;">📍 {minfo.get('venue','N/A')} &nbsp;|&nbsp; 🏆 Winner: <b style="color:#f0a500;">{minfo.get('winner','N/A')}</b></p>
</div>""", unsafe_allow_html=True)

elif page == "🤖 Win Predictor":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">🤖 Win Predictor</h1>', unsafe_allow_html=True)
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
        
        @st.cache_data
        def train_model():
            try:
                df = matches.dropna(subset=['winner']).copy()
                
                # Encode teams - fit on both team1 and team2
                le_t = LabelEncoder()
                all_teams = pd.concat([df['team1'], df['team2']]).unique()
                le_t.fit(all_teams)
                
                # Encode venue
                le_v = LabelEncoder()
                le_v.fit(df['venue'].dropna().unique())
                
                # Create features
                df['t1e'] = le_t.transform(df['team1'])
                df['t2e'] = le_t.transform(df['team2'])
                df['ve'] = le_v.transform(df['venue'].fillna('Unknown'))
                df['tw'] = (df['toss_winner'] == df['team1']).astype(int)
                df['de'] = (df['toss_decision'] == 'bat').astype(int)
                df['we'] = (df['winner'] == df['team1']).astype(int)
                
                # Train model
                X = df[['t1e', 't2e', 've', 'tw', 'de']]
                y = df['we']
                
                clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
                clf.fit(X, y)
                
                return clf, le_t, le_v
            except Exception as e:
                st.error(f"Model training error: {e}")
                return None, None, None
        
        clf, le_t, le_v = train_model()
        
        if clf is None:
            st.error("Failed to train prediction model")
        else:
            tl = sorted(matches['team1'].dropna().unique().tolist())
            vl = sorted(matches['venue'].dropna().unique().tolist())
            
            st.markdown("### Select Match Details")
            c1, c2 = st.columns(2)
            
            with c1:
                pt1 = st.selectbox("🏏 Team 1", tl, index=0, key="team1_sel")
                pv = st.selectbox("🏟️ Venue", vl, index=0 if vl else None, key="venue_sel")
                ptw = st.radio("🪙 Toss Winner", [pt1, "Team 2"], key="toss_winner_sel")
            
            with c2:
                pt2_options = [t for t in tl if t != pt1]
                pt2 = st.selectbox("🏏 Team 2", pt2_options, index=0 if pt2_options else None, key="team2_sel")
                pd_ = st.radio("📋 Toss Decision", ["Bat", "Field"], key="toss_decision_sel")
            
            if st.button("🔮 Predict Winner", use_container_width=True):
                try:
                    if not pt1 or not pt2 or not pv:
                        st.error("❌ Please select all required fields")
                    else:
                        # Encode inputs
                        t1e = le_t.transform([pt1])[0]
                        t2e = le_t.transform([pt2])[0]
                        
                        # Handle venue encoding
                        try:
                            ve = le_v.transform([pv])[0]
                        except:
                            ve = le_v.transform(['Unknown'])[0] if 'Unknown' in le_v.classes_ else 0
                        
                        tw = 1 if ptw == pt1 else 0
                        de = 1 if pd_ == "Bat" else 0
                        
                        # Make prediction
                        features = [[t1e, t2e, ve, tw, de]]
                        prob = clf.predict_proba(features)[0]
                        
                        # Get probabilities (prob[1] = team1 win, prob[0] = team2 win)
                        p1 = round(prob[1] * 100, 1)
                        p2 = round(prob[0] * 100, 1)
                        
                        # Get logos
                        l1 = TEAM_LOGOS.get(pt1, "")
                        l2 = TEAM_LOGOS.get(pt2, "")
                        li1 = f'<img src="{l1}" style="width:52px;height:52px;object-fit:contain;margin-bottom:10px;" alt="{pt1}" />' if l1 else "🏏"
                        li2 = f'<img src="{l2}" style="width:52px;height:52px;object-fit:contain;margin-bottom:10px;" alt="{pt2}" />' if l2 else "🏏"
                        
                        # Display results
                        st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d1f3c,#071526);border:2px solid #f0a500;border-radius:20px;padding:28px;text-align:center;margin:16px 0;">
  <div style="font-family:'Rajdhani',sans-serif;font-size:20px;font-weight:700;color:#f0a500;margin-bottom:20px;letter-spacing:2px;">🔮 PREDICTION RESULTS</div>
  <div style="display:flex;justify-content:space-around;align-items:center;">
    <div>{li1}<div style="font-family:'Rajdhani',sans-serif;font-size:44px;font-weight:700;color:#0077b6;">{p1}%</div><div style="color:rgba(255,255,255,0.6);font-size:14px;">{pt1}</div></div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:22px;color:rgba(255,255,255,0.2);">VS</div>
    <div>{li2}<div style="font-family:'Rajdhani',sans-serif;font-size:44px;font-weight:700;color:#f0a500;">{p2}%</div><div style="color:rgba(255,255,255,0.6);font-size:14px;">{pt2}</div></div>
  </div>
</div>""", unsafe_allow_html=True)
                        
                        # Show chart
                        fig = go.Figure(go.Bar(
                            x=[p1, p2],
                            y=[pt1, pt2],
                            orientation='h',
                            marker_color=['#0077b6', '#f0a500'],
                            text=[f"{p1}%", f"{p2}%"],
                            textposition='inside',
                            textfont=dict(size=16, color='white'),
                            hovertemplate="<b>%{y}</b><br>Win Probability: %{x:.1f}%<extra></extra>"
                        ))
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            hoverlabel=HOVER,
                            xaxis_range=[0, 100],
                            showlegend=False,
                            font=dict(color='white'),
                            xaxis_title="Win Probability %",
                            yaxis_title="Team"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show match details
                        st.markdown("### Match Summary")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("🏏 Team 1", pt1)
                        col2.metric("🏏 Team 2", pt2)
                        col3.metric("🏟️ Venue", pv)
                        col4.metric("🪙 Toss Winner", ptw)
                        
                except Exception as e:
                    st.error(f"❌ Prediction error: {str(e)}")
    
    except ImportError:
        st.warning("⚠️ Required package missing. Run: pip install scikit-learn")

elif page == "📤 Export Data":
    st.markdown('<h1 style="font-family:Rajdhani,sans-serif;color:#f0a500;">📤 Export Data</h1>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### 🏏 Matches")
        st.dataframe(filtered_matches.head(20),use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download Matches CSV",filtered_matches.to_csv(index=False).encode(),"ipl_matches.csv","text/csv",use_container_width=True)
    with c2:
        st.markdown("#### 🎳 Deliveries")
        st.dataframe(filtered_deliveries.head(20),use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download Deliveries CSV",filtered_deliveries.head(5000).to_csv(index=False).encode(),"ipl_deliveries.csv","text/csv",use_container_width=True)