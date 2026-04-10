import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json, os


# Streamlit page config — has to be the first Streamlit call in the script
st.set_page_config(
    page_title="Mastodon Sentiment Dashboard",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----- Custom CSS block -----
# Dropped the whole thing in one st.markdown so Streamlit doesn't re-render it on every
# interaction. Going for a light cream look because the storm dashboard was already dark
# and I wanted something visually different for this project.
st.markdown("""
<style>
/* Fonts from Google */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Grotesk:wght@400;500;600;700&family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&display=swap');

/* Design tokens kept in one place — easier to tweak later */
:root {
    --masto-bg:         #f8f7f4;
    --masto-surface:    #ffffff;
    --masto-card:       #ffffff;
    --masto-border:     #e8e5de;
    --masto-border-h:   #d4d0c8;
    --masto-purple:     #6364ff;
    --masto-indigo:     #563acc;
    --masto-teal:       #17b890;
    --masto-coral:      #ff6b6b;
    --masto-amber:      #f0a500;
    --masto-sky:        #4ecdc4;
    --masto-pink:       #ee5a9e;
    --masto-text:       #2d2a26;
    --masto-text-sec:   #6b6560;
    --masto-text-muted: #9e9891;
    --shadow-sm:        0 1px 3px rgba(45,42,38,0.06);
    --shadow-md:        0 4px 16px rgba(45,42,38,0.08);
    --shadow-lg:        0 8px 32px rgba(45,42,38,0.10);
    --shadow-glow-p:    0 4px 20px rgba(99,100,255,0.15);
    --shadow-glow-t:    0 4px 20px rgba(23,184,144,0.15);
    --shadow-glow-c:    0 4px 20px rgba(255,107,107,0.15);
    --radius:           16px;
    --radius-sm:        10px;
}

/* App background */
.stApp {
    background: var(--masto-bg) !important;
}

/* Very faint dot grid across the whole page */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: radial-gradient(circle, #d4d0c8 0.7px, transparent 0.7px);
    background-size: 28px 28px;
    opacity: 0.35;
    pointer-events: none;
    z-index: 0;
}

/* Sidebar — went a bit overboard here with the glassy look but I liked how it turned out */
section[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 20% 0%, rgba(99,100,255,0.12) 0%, transparent 45%),
        radial-gradient(circle at 80% 100%, rgba(23,184,144,0.10) 0%, transparent 45%),
        radial-gradient(circle at 50% 50%, rgba(238,90,158,0.06) 0%, transparent 60%),
        linear-gradient(165deg, #ffffff 0%, #faf8f3 50%, #f5f0ff 100%) !important;
    border-right: 1px solid rgba(99,100,255,0.15) !important;
    box-shadow: 4px 0 24px rgba(99,100,255,0.06);
}

/* Coloured strip along the top edge of the sidebar */
section[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #6364ff 0%, #17b890 35%, #f0a500 65%, #ee5a9e 100%);
    z-index: 10;
}

/* Soft glowing blob that drifts up and down behind the filters */
section[data-testid="stSidebar"]::after {
    content: '';
    position: absolute;
    top: 30%; right: -60px;
    width: 160px; height: 160px;
    background: radial-gradient(circle, rgba(99,100,255,0.15) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
    filter: blur(20px);
    animation: float 12s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0) scale(1); }
    50%      { transform: translateY(-20px) scale(1.08); }
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.2rem;
}

/* Sidebar heading with a purple-to-pink gradient fill */
section[data-testid="stSidebar"] .stMarkdown h2 {
    background: linear-gradient(135deg, #6364ff 0%, #ee5a9e 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.55rem !important;
    letter-spacing: -0.5px !important;
    margin-bottom: 0.25rem !important;
}

/* Labels that sit above each filter widget */
section[data-testid="stSidebar"] label {
    color: var(--masto-text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.3px !important;
    text-transform: none !important;
    margin-bottom: 4px !important;
    display: inline-block !important;
}

/* Kill Streamlit's default sidebar HR since I'm using my own */
section[data-testid="stSidebar"] hr {
    display: none !important;
}

/* Each multiselect wrapped in a frosted-glass card */
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.8);
    border-radius: 16px;
    padding: 14px 14px 12px;
    margin-bottom: 14px;
    box-shadow:
        0 1px 3px rgba(45,42,38,0.04),
        inset 0 1px 0 rgba(255,255,255,0.9);
    transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #6364ff, #ee5a9e);
    opacity: 0;
    transition: opacity 0.35s ease;
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:hover {
    background: rgba(255,255,255,0.9);
    border-color: rgba(99,100,255,0.3);
    transform: translateX(2px);
    box-shadow:
        0 8px 24px rgba(99,100,255,0.10),
        inset 0 1px 0 rgba(255,255,255,1);
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:hover::before {
    opacity: 1;
}

/* Different left-bar colour for each of the three filter cards */
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:nth-of-type(1)::before {
    background: linear-gradient(180deg, #6364ff, #8b8cff);
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:nth-of-type(2)::before {
    background: linear-gradient(180deg, #17b890, #4ecdc4);
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:nth-of-type(3)::before {
    background: linear-gradient(180deg, #f0a500, #ee5a9e);
}

/* The input box inside each multiselect */
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] > div > div {
    background: rgba(255,255,255,0.7) !important;
    border: 1.5px solid rgba(99,100,255,0.15) !important;
    border-radius: 12px !important;
    min-height: 44px !important;
    transition: all 0.3s ease !important;
    box-shadow: inset 0 1px 2px rgba(45,42,38,0.03) !important;
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] > div > div:hover {
    border-color: rgba(99,100,255,0.4) !important;
    background: rgba(255,255,255,0.95) !important;
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] > div > div:focus-within {
    border-color: #6364ff !important;
    box-shadow:
        0 0 0 4px rgba(99,100,255,0.12),
        inset 0 1px 2px rgba(45,42,38,0.03) !important;
    background: #ffffff !important;
}

/* Selected items appear as gradient pills */
section[data-testid="stSidebar"] span[data-baseweb="tag"] {
    background: linear-gradient(135deg, #6364ff 0%, #8b8cff 100%) !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    padding: 3px 4px 3px 10px !important;
    box-shadow:
        0 2px 6px rgba(99,100,255,0.25),
        inset 0 1px 0 rgba(255,255,255,0.25) !important;
    transition: all 0.25s ease !important;
    margin: 2px !important;
}
section[data-testid="stSidebar"] span[data-baseweb="tag"]:hover {
    transform: translateY(-1px) scale(1.03) !important;
    box-shadow:
        0 4px 12px rgba(99,100,255,0.35),
        inset 0 1px 0 rgba(255,255,255,0.25) !important;
}
section[data-testid="stSidebar"] span[data-baseweb="tag"] span {
    color: #ffffff !important;
    font-weight: 600 !important;
}
/* The little x to remove a pill */
section[data-testid="stSidebar"] span[data-baseweb="tag"] span[role="button"] {
    background: rgba(255,255,255,0.25) !important;
    border-radius: 6px !important;
    margin-left: 4px !important;
    padding: 0 4px !important;
    transition: background 0.2s ease !important;
}
section[data-testid="stSidebar"] span[data-baseweb="tag"] span[role="button"]:hover {
    background: rgba(255,255,255,0.45) !important;
}

/* Sentiment filter pills use teal instead of purple */
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:nth-of-type(2) span[data-baseweb="tag"] {
    background: linear-gradient(135deg, #17b890 0%, #4ecdc4 100%) !important;
    box-shadow:
        0 2px 6px rgba(23,184,144,0.25),
        inset 0 1px 0 rgba(255,255,255,0.25) !important;
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:nth-of-type(2) span[data-baseweb="tag"]:hover {
    box-shadow:
        0 4px 12px rgba(23,184,144,0.35),
        inset 0 1px 0 rgba(255,255,255,0.25) !important;
}

/* Language filter pills go amber → pink */
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:nth-of-type(3) span[data-baseweb="tag"] {
    background: linear-gradient(135deg, #f0a500 0%, #ee5a9e 100%) !important;
    box-shadow:
        0 2px 6px rgba(240,165,0,0.25),
        inset 0 1px 0 rgba(255,255,255,0.25) !important;
}
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:nth-of-type(3) span[data-baseweb="tag"]:hover {
    box-shadow:
        0 4px 12px rgba(238,90,158,0.35),
        inset 0 1px 0 rgba(255,255,255,0.25) !important;
}

/* Popover menu that opens when you click a multiselect */
div[data-baseweb="popover"] ul {
    background: rgba(255,255,255,0.98) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(99,100,255,0.2) !important;
    border-radius: 14px !important;
    box-shadow: 0 12px 40px rgba(45,42,38,0.15) !important;
    padding: 6px !important;
}
div[data-baseweb="popover"] ul li {
    border-radius: 9px !important;
    margin: 2px 0 !important;
    padding: 8px 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    color: var(--masto-text) !important;
    transition: all 0.2s ease !important;
}
div[data-baseweb="popover"] ul li:hover {
    background: linear-gradient(90deg, rgba(99,100,255,0.1), rgba(238,90,158,0.08)) !important;
    color: var(--masto-purple) !important;
    transform: translateX(3px);
}

.filter-card-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--masto-text-sec);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Little info card that sits under the filters */
.sidebar-info-card {
    background: linear-gradient(135deg, rgba(99,100,255,0.08) 0%, rgba(238,90,158,0.06) 100%);
    border: 1px solid rgba(99,100,255,0.15);
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 18px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.sidebar-info-card::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 40px; height: 3px;
    background: linear-gradient(90deg, #6364ff, #ee5a9e);
    border-radius: 0 0 3px 3px;
}
.sidebar-info-card .pulse-dot {
    display: inline-block;
    width: 7px; height: 7px;
    background: #17b890;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s ease-in-out infinite;
    box-shadow: 0 0 0 0 rgba(23,184,144,0.6);
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(23,184,144,0.6); }
    70%  { box-shadow: 0 0 0 8px rgba(23,184,144,0); }
    100% { box-shadow: 0 0 0 0 rgba(23,184,144,0); }
}
.sidebar-info-card .info-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.78rem;
    color: var(--masto-text);
    margin-bottom: 3px;
}
.sidebar-info-card .info-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    color: var(--masto-text-muted);
    line-height: 1.4;
}

/* Brand card at the top of the sidebar with a spinning halo behind it */
.sidebar-brand {
    background: linear-gradient(135deg, #ffffff 0%, #faf8ff 100%);
    border: 1px solid rgba(99,100,255,0.15);
    border-radius: 18px;
    padding: 18px 16px;
    margin-bottom: 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(99,100,255,0.08);
}
.sidebar-brand::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: conic-gradient(from 0deg,
        rgba(99,100,255,0.08),
        rgba(23,184,144,0.08),
        rgba(240,165,0,0.08),
        rgba(238,90,158,0.08),
        rgba(99,100,255,0.08));
    animation: rotate 20s linear infinite;
    pointer-events: none;
}
.sidebar-brand > * { position: relative; z-index: 1; }
@keyframes rotate {
    to { transform: rotate(360deg); }
}
.sidebar-brand .brand-emoji {
    font-size: 2.2rem;
    display: block;
    margin-bottom: 4px;
    filter: drop-shadow(0 2px 8px rgba(99,100,255,0.25));
}
.sidebar-brand .brand-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 800;
    font-size: 1.15rem;
    background: linear-gradient(135deg, #6364ff 0%, #ee5a9e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.3px;
    margin-bottom: 2px;
}
.sidebar-brand .brand-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    color: var(--masto-text-muted);
    letter-spacing: 0.3px;
    text-transform: uppercase;
    font-weight: 500;
}

/* Thin gradient divider in the sidebar */
.sidebar-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,100,255,0.3), transparent);
    margin: 16px 0 14px;
    border: none;
}

/* Headings in the main content area */
.stApp h1 {
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px !important;
    color: var(--masto-text) !important;
    font-size: 2rem !important;
    -webkit-text-fill-color: unset !important;
}
.stApp h2, .stApp h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--masto-text) !important;
    font-weight: 600 !important;
    letter-spacing: -0.2px;
}
.stApp p, .stApp span, .stApp div, .stApp label {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--masto-text) !important;
}

/* Metric cards across the top of the page */
div[data-testid="stMetric"] {
    background: var(--masto-card);
    border: 1px solid var(--masto-border);
    border-radius: var(--radius);
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease, border-color 0.3s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-md);
    border-color: var(--masto-purple);
}
div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 0 0 var(--radius) var(--radius);
}
div[data-testid="stMetric"] label {
    color: var(--masto-text-muted) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 0.72rem !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--masto-text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.65rem !important;
}

/* Bottom accent bar colour changes per metric card */
div[data-testid="stMetric"]:nth-of-type(1)::before { background: linear-gradient(90deg, #6364ff, #8b8cff); }
div[data-testid="stMetric"]:nth-of-type(2)::before { background: linear-gradient(90deg, #17b890, #4ecdc4); }
div[data-testid="stMetric"]:nth-of-type(3)::before { background: linear-gradient(90deg, #f0a500, #ffc857); }
div[data-testid="stMetric"]:nth-of-type(4)::before { background: linear-gradient(90deg, #4ecdc4, #7be0d6); }
div[data-testid="stMetric"]:nth-of-type(5)::before { background: linear-gradient(90deg, #ff6b6b, #ff9e9e); }
div[data-testid="stMetric"]:nth-of-type(1):hover { box-shadow: var(--shadow-glow-p); border-color: #6364ff; }
div[data-testid="stMetric"]:nth-of-type(2):hover { box-shadow: var(--shadow-glow-t); border-color: #17b890; }
div[data-testid="stMetric"]:nth-of-type(3):hover { box-shadow: 0 4px 20px rgba(240,165,0,0.15); border-color: #f0a500; }
div[data-testid="stMetric"]:nth-of-type(4):hover { box-shadow: var(--shadow-glow-t); border-color: #4ecdc4; }
div[data-testid="stMetric"]:nth-of-type(5):hover { box-shadow: var(--shadow-glow-c); border-color: #ff6b6b; }

/* Plotly chart frames */
div[data-testid="stPlotlyChart"] {
    background: var(--masto-card);
    border: 1px solid var(--masto-border);
    border-radius: var(--radius);
    padding: 14px;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
div[data-testid="stPlotlyChart"]:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--masto-border-h);
}

.stApp h3 {
    margin-bottom: 8px !important;
}

/* Dataframe tables */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--masto-border);
    border-radius: var(--radius-sm);
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

/* Horizontal rules in the main body */
.stApp > div hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--masto-border), var(--masto-purple), var(--masto-border), transparent) !important;
    margin: 1.8rem 0 !important;
    opacity: 0.6;
}

/* Thin scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--masto-bg); }
::-webkit-scrollbar-thumb { background: var(--masto-border-h); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--masto-purple); }

/* Hero banner area at the top of the page */
.hero-banner {
    background: linear-gradient(135deg, #ffffff 0%, #f0eef9 40%, #e8f6f2 70%, #fff8eb 100%);
    border: 1px solid var(--masto-border);
    border-radius: 22px;
    padding: 32px 40px;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -40%; right: -10%;
    width: 350px; height: 350px;
    background: radial-gradient(circle, rgba(99,100,255,0.06) 0%, transparent 60%);
    pointer-events: none;
}
.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -30%; left: 10%;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(23,184,144,0.05) 0%, transparent 60%);
    pointer-events: none;
}
.hero-emoji {
    font-size: 2.6rem;
    margin-bottom: 6px;
    display: block;
}
.hero-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 800;
    font-size: 2.3rem;
    color: var(--masto-text);
    margin: 0 0 8px;
    letter-spacing: -0.5px;
    line-height: 1.15;
}
.hero-title .accent { color: var(--masto-purple); }
.hero-sub {
    font-family: 'DM Sans', sans-serif;
    color: var(--masto-text-sec);
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,100,255,0.08);
    border: 1px solid rgba(99,100,255,0.2);
    color: var(--masto-purple);
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: 4px 14px;
    border-radius: 20px;
    margin-bottom: 16px;
}

/* Little header row that sits above each chart */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 8px 0 6px;
}
.section-icon {
    width: 38px; height: 38px;
    border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem;
}
.section-label {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--masto-text);
    letter-spacing: -0.1px;
}

/* Stat cards used in the ML results section */
.model-card {
    background: linear-gradient(135deg, #f8f7f4 0%, #f0eef9 100%);
    border: 1px solid var(--masto-border);
    border-radius: var(--radius);
    padding: 20px 24px;
    text-align: center;
    box-shadow: var(--shadow-sm);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.model-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.model-card-label {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--masto-text-muted);
    margin-bottom: 6px;
}
.model-card-value {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.8rem;
    color: var(--masto-text);
}
.model-card-note {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: var(--masto-text-muted);
    margin-top: 4px;
}

/* Footer strip */
.footer-text {
    text-align: center;
    color: var(--masto-text-muted);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    padding: 2rem 0 1rem;
    letter-spacing: 0.2px;
}
.footer-text a { color: var(--masto-purple); text-decoration: none; font-weight: 500; }
.footer-text a:hover { text-decoration: underline; }
</style>
""", unsafe_allow_html=True)


# ----- Plotly defaults -----
# Every chart pulls these values so the fonts, margins and transparent bg stay consistent.
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#6b6560", size=13),
    margin=dict(l=40, r=20, t=40, b=40),
)
GRID_COLOR = "rgba(232,229,222,0.7)"

def apply_axes(fig):
    # Little shortcut, nothing fancy
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    return fig

PALETTE = ["#6364ff", "#17b890", "#ff6b6b", "#f0a500", "#4ecdc4", "#ee5a9e", "#563acc", "#ffc857"]
# Fixed mapping so positive is always green, negative always red, etc — otherwise Plotly picks
# whatever it wants and the colours swap between runs which was really confusing during testing
SENTIMENT_COLORS = {"positive": "#17b890", "neutral": "#f0a500", "negative": "#ff6b6b"}


# ----- Data loading -----
DATA_PATH = "processed/mastodon_with_sentiment.csv"
RESULTS_PATH = "results/results_summary.json"

@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error(f"Missing file: {DATA_PATH}. Run the sentiment notebook first to generate it.")
        st.stop()
    return pd.read_csv(DATA_PATH, parse_dates=["posted_at"])

@st.cache_data
def load_results():
    # Results file is optional — if the modelling step hasn't run yet, just skip that section
    if not os.path.exists(RESULTS_PATH):
        return {}
    with open(RESULTS_PATH) as f:
        return json.load(f)

posts = load_data()
results = load_results()


# ----- Sidebar -----
with st.sidebar:
    # Brand header, purely decorative
    st.markdown("""
    <div class="sidebar-brand">
        <span class="brand-emoji">🐘</span>
        <div class="brand-title">Mastodon Insights</div>
        <div class="brand-sub">Control Center</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Refine View")
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    all_topics = posts["topic_query"].unique().tolist()
    topics = st.multiselect(
        "🏷️  Topics",
        options=all_topics,
        default=all_topics,
        help="Filter posts by topic category",
    )

    sentiments_opt = ["positive", "neutral", "negative"]
    sentiments = st.multiselect(
        "💬  Sentiment Classes",
        options=sentiments_opt,
        default=sentiments_opt,
        help="Filter by predicted sentiment label",
    )

    # Language list gets capped at 10 — the long tail is mostly junk with 2-3 posts each
    top_langs = posts["language"].value_counts().head(10).index.tolist()
    languages = st.multiselect(
        "🌐  Languages",
        options=top_langs,
        default=[],
        help="Optional: restrict to specific languages (top 10 shown)",
    )

    # Small status card at the bottom so there's something under the filters
    st.markdown("""
    <div class="sidebar-info-card">
        <div class="info-title"><span class="pulse-dot"></span>Live Filtering</div>
        <div class="info-sub">All charts update instantly as you adjust the filters above</div>
    </div>
    """, unsafe_allow_html=True)

# Single boolean mask built from the sidebar selections
df = posts[posts["topic_query"].isin(topics) & posts["final_sentiment"].isin(sentiments)]
if languages:
    df = df[df["language"].isin(languages)]


# ----- Hero banner at the top of the main area -----
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">MSc Data Science · 7150CEM · Coventry University</div>
    <span class="hero-emoji">🐘</span>
    <h1 class="hero-title">Mastodon <span class="accent">Sentiment</span> Analysis</h1>
    <p class="hero-sub">Real-time social sentiment tracking across topics, languages &amp; engagement patterns on the decentralised web</p>
</div>
""", unsafe_allow_html=True)

st.markdown("")


# ----- KPI strip -----
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("Total Posts", f"{len(df):,}")
with m2:
    st.metric("Languages", f"{df['language'].nunique()}")
with m3:
    st.metric("Avg Engagement", f"{df['total_engagement'].mean():.1f}")
with m4:
    pos_pct = (df["final_sentiment"] == "positive").mean() * 100
    st.metric("Positive %", f"{pos_pct:.1f}%")
with m5:
    neg_pct = (df["final_sentiment"] == "negative").mean() * 100
    st.metric("Negative %", f"{neg_pct:.1f}%")

st.markdown("---")


# ----- Sentiment overview row -----
c1, c2 = st.columns(2)

with c1:
    st.markdown(
        '<div class="section-header">'
        '<div class="section-icon" style="background:rgba(99,100,255,0.08);">💬</div>'
        '<span class="section-label">Sentiment Distribution</span></div>',
        unsafe_allow_html=True,
    )
    sent_c = df["final_sentiment"].value_counts()
    fig1 = go.Figure(
        go.Pie(
            labels=sent_c.index,
            values=sent_c.values,
            hole=0.55,
            marker=dict(
                colors=[SENTIMENT_COLORS.get(s, "#ccc") for s in sent_c.index],
                line=dict(color="#ffffff", width=3),
            ),
            textfont=dict(color="#2d2a26", size=13, family="DM Sans, sans-serif"),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Posts: %{value:,}<br>Share: %{percent}<extra></extra>",
        )
    )
    fig1.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown(
        '<div class="section-header">'
        '<div class="section-icon" style="background:rgba(23,184,144,0.08);">🏷️</div>'
        '<span class="section-label">Sentiment by Topic</span></div>',
        unsafe_allow_html=True,
    )
    # normalize="index" gives me row percentages, so each topic stacks to 100%
    ct = pd.crosstab(df["topic_query"], df["final_sentiment"], normalize="index") * 100
    fig2 = go.Figure()
    for sent, colour in [("positive", "#17b890"), ("neutral", "#f0a500"), ("negative", "#ff6b6b")]:
        if sent in ct.columns:
            fig2.add_trace(go.Bar(
                name=sent.capitalize(), x=ct.index, y=ct[sent],
                marker_color=colour, marker_line_width=0, opacity=0.88,
                hovertemplate="<b>%{x}</b><br>" + sent.capitalize() + ": %{y:.1f}%<extra></extra>",
            ))
    fig2.update_layout(**PLOTLY_LAYOUT, height=420, barmode="stack",
                       legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12, color="#6b6560"),
                                   orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    fig2.update_yaxes(title_text="Percentage (%)", gridcolor=GRID_COLOR)
    fig2.update_xaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig2, use_container_width=True)


# ----- Engagement and language row -----
c3, c4 = st.columns(2)

with c3:
    st.markdown(
        '<div class="section-header">'
        '<div class="section-icon" style="background:rgba(240,165,0,0.08);">📊</div>'
        '<span class="section-label">Engagement by Topic</span></div>',
        unsafe_allow_html=True,
    )
    # Sort ascending so the biggest bar ends up at the top of the horizontal chart
    eng = df.groupby("topic_query")["total_engagement"].mean().sort_values()
    fig3 = go.Figure(go.Bar(
        x=eng.values, y=eng.index, orientation="h",
        marker=dict(
            color=eng.values,
            colorscale=[[0, "#e8f6f2"], [0.5, "#4ecdc4"], [1, "#17b890"]],
            line=dict(width=0),
        ),
        hovertemplate="<b>%{y}</b><br>Avg Engagement: %{x:.1f}<extra></extra>",
    ))
    fig3.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False)
    fig3.update_xaxes(title_text="Mean Engagement", gridcolor=GRID_COLOR)
    fig3.update_yaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.markdown(
        '<div class="section-header">'
        '<div class="section-icon" style="background:rgba(86,58,204,0.08);">🌐</div>'
        '<span class="section-label">Language Distribution</span></div>',
        unsafe_allow_html=True,
    )
    lang_top = df["language"].value_counts().head(10)
    fig4 = go.Figure(go.Bar(
        x=lang_top.index, y=lang_top.values,
        marker=dict(
            color=lang_top.values,
            colorscale=[[0, "#f0eef9"], [0.5, "#8b8cff"], [1, "#6364ff"]],
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b><br>Posts: %{y:,}<extra></extra>",
    ))
    fig4.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False)
    fig4.update_xaxes(title_text="Language", gridcolor=GRID_COLOR)
    fig4.update_yaxes(title_text="Posts", gridcolor=GRID_COLOR)
    st.plotly_chart(fig4, use_container_width=True)


# ----- Posting activity heatmap -----
st.markdown(
    '<div class="section-header">'
    '<div class="section-icon" style="background:rgba(238,90,158,0.08);">🕐</div>'
    '<span class="section-label">Posting Activity Heatmap</span></div>',
    unsafe_allow_html=True,
)
if "post_hour" in df.columns and "post_weekday" in df.columns:
    # Weekdays come out of pandas in alphabetical order by default which looks terrible,
    # so I force Mon → Sun with reindex
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heat = pd.crosstab(df["post_weekday"], df["post_hour"]).reindex(dow_order).fillna(0)
    fig5 = px.imshow(
        heat, color_continuous_scale=[[0, "#f8f7f4"], [0.3, "#fce4b6"], [0.6, "#f0a500"], [1.0, "#ee5a9e"]],
        labels=dict(x="Hour (UTC)", y="Day", color="Posts"),
    )
    fig5.update_layout(**PLOTLY_LAYOUT, height=340)
    st.plotly_chart(fig5, use_container_width=True)


# ----- Sentiment scores and engagement comparison row -----
c5, c6 = st.columns(2)

with c5:
    st.markdown(
        '<div class="section-header">'
        '<div class="section-icon" style="background:rgba(255,107,107,0.08);">📈</div>'
        '<span class="section-label">Sentiment Score Distribution</span></div>',
        unsafe_allow_html=True,
    )
    if "vader_compound" in df.columns:
        # Overlay three histograms on the same axes, one per sentiment class,
        # with some transparency so you can see where they overlap
        fig6 = go.Figure()
        for sent, color in SENTIMENT_COLORS.items():
            subset = df[df["final_sentiment"] == sent]
            if len(subset) > 0:
                fig6.add_trace(go.Histogram(
                    x=subset["vader_compound"], name=sent.capitalize(),
                    marker_color=color, opacity=0.7, nbinsx=40,
                    hovertemplate="Score: %{x:.2f}<br>Count: %{y}<extra></extra>",
                ))
        fig6.update_layout(**PLOTLY_LAYOUT, height=400, barmode="overlay",
                           legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#6b6560"),
                                       orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
        fig6.update_xaxes(title_text="VADER Compound Score", gridcolor=GRID_COLOR)
        fig6.update_yaxes(title_text="Count", gridcolor=GRID_COLOR)
        st.plotly_chart(fig6, use_container_width=True)

with c6:
    st.markdown(
        '<div class="section-header">'
        '<div class="section-icon" style="background:rgba(78,205,196,0.08);">🔗</div>'
        '<span class="section-label">Engagement vs Sentiment</span></div>',
        unsafe_allow_html=True,
    )
    # Mean, median and std per class — std feeds the error bars
    eng_sent = df.groupby("final_sentiment")["total_engagement"].agg(["mean", "median", "std"]).reindex(
        ["positive", "neutral", "negative"]
    )
    fig7 = go.Figure()
    colors_bar = [SENTIMENT_COLORS.get(s, "#ccc") for s in eng_sent.index]
    fig7.add_trace(go.Bar(
        x=[s.capitalize() for s in eng_sent.index], y=eng_sent["mean"],
        marker_color=colors_bar, marker_line_width=0, opacity=0.85,
        error_y=dict(type="data", array=eng_sent["std"].fillna(0).values, visible=True, color="#9e9891", thickness=1.5),
        hovertemplate="<b>%{x}</b><br>Mean: %{y:.2f}<extra></extra>",
    ))
    fig7.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
    fig7.update_xaxes(title_text="Sentiment", gridcolor=GRID_COLOR)
    fig7.update_yaxes(title_text="Mean Engagement", gridcolor=GRID_COLOR)
    st.plotly_chart(fig7, use_container_width=True)


# ----- Model performance section -----
# This whole block is hidden unless results_summary.json exists AND has engagement_model in it
if results:
    eng_res = results.get("engagement_model", {})
    if eng_res:
        st.markdown("---")
        st.markdown(
            '<div class="section-header" style="margin-bottom:16px;">'
            '<div class="section-icon" style="background:rgba(99,100,255,0.08);">🤖</div>'
            '<span class="section-label" style="font-size:1.25rem;">Engagement Prediction Model</span></div>',
            unsafe_allow_html=True,
        )

        # Tiny parser because the JSON from the notebook sometimes writes values
        # as "14.436" strings instead of floats. Also handles dollar signs just in case.
        def _to_num(val):
            if val is None:
                return np.nan
            try:
                return float(str(val).replace("$", "").replace(",", ""))
            except ValueError:
                return np.nan

        rmse_val = _to_num(eng_res.get("RMSE"))
        mae_val = _to_num(eng_res.get("MAE"))
        r2_val = _to_num(eng_res.get("R2"))

        # Traffic-light colouring on R2: green if the model actually learned something,
        # amber if it's weak, red if it's worse than predicting the mean
        r2_color = "#17b890" if r2_val and r2_val > 0.3 else ("#f0a500" if r2_val and r2_val > 0 else "#ff6b6b")
        r2_note = "Good fit" if r2_val and r2_val > 0.3 else ("Weak fit" if r2_val and r2_val > 0 else "Negative — baseline outperforms")

        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            st.markdown(f"""
            <div class="model-card">
                <div class="model-card-label">Root Mean Squared Error</div>
                <div class="model-card-value" style="color:#6364ff;">{rmse_val:.3f}</div>
                <div class="model-card-note">Lower is better</div>
            </div>""", unsafe_allow_html=True)
        with rc2:
            st.markdown(f"""
            <div class="model-card">
                <div class="model-card-label">Mean Absolute Error</div>
                <div class="model-card-value" style="color:#17b890;">{mae_val:.3f}</div>
                <div class="model-card-note">Avg prediction error</div>
            </div>""", unsafe_allow_html=True)
        with rc3:
            st.markdown(f"""
            <div class="model-card">
                <div class="model-card-label">R² Score</div>
                <div class="model-card-value" style="color:{r2_color};">{r2_val:.4f}</div>
                <div class="model-card-note">{r2_note}</div>
            </div>""", unsafe_allow_html=True)

        # Side-by-side RMSE vs MAE bar chart underneath the three cards
        st.markdown("")
        fig_model = go.Figure()
        metrics_names = ["RMSE", "MAE"]
        metrics_vals = [rmse_val, mae_val]
        metrics_colors = ["#6364ff", "#17b890"]
        fig_model.add_trace(go.Bar(
            x=metrics_names, y=metrics_vals,
            marker_color=metrics_colors, marker_line_width=0, opacity=0.85,
            text=[f"{v:.3f}" for v in metrics_vals], textposition="outside",
            textfont=dict(color="#2d2a26", size=14, family="Space Grotesk"),
            hovertemplate="<b>%{x}</b>: %{y:.3f}<extra></extra>",
        ))
        fig_model.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
                                title=dict(text="Error Metrics Comparison",
                                           font=dict(size=13, color="#6b6560")))
        apply_axes(fig_model)
        st.plotly_chart(fig_model, use_container_width=True)


# ----- Footer -----
st.markdown("---")
st.markdown(
    '<div class="footer-text">'
    '🐘 Dashboard built for <strong>MSc Data Science Project (7150CEM)</strong> — '
    'Coventry University<br>'
    'Data source: <a href="https://joinmastodon.org/" target="_blank">'
    'Mastodon Public API</a> · Powered by Streamlit & Plotly'
    '</div>',
    unsafe_allow_html=True,
)