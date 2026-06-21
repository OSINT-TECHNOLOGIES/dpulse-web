import streamlit as st
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import re
import time
import os
import json
import pandas as pd
from datetime import datetime

class SnapshotMode(str, Enum):
    NONE = "n"
    SCREENSHOT = "s"
    PAGE_COPY = "p"
    WAYBACK = "w"

@dataclass
class ScanConfig:
    domain: str = ""
    url: str = ""
    comment: str = ""
    page_search: bool = False
    keywords: List[str] = field(default_factory=list)
    dorking_mode: str = "n"
    api_ids: List[str] = field(default_factory=lambda: ["Empty"])
    snapshot_mode: SnapshotMode = SnapshotMode.NONE
    username: Optional[str] = None
    wb_from: str = "N"
    wb_to: str = "N"

if "config" not in st.session_state:
    st.session_state.config = ScanConfig()
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None

def validate_domain(domain: str) -> bool:
    pattern = r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain))

def compute_dork_mark(mode: str) -> str:
    if mode == "n":
        return "No dorking"
    if mode.startswith("custom+"):
        return f"Custom ({mode.split('+')[1]})"
    mapping = {
        "basic": "Basic",
        "iot": "IoT",
        "files": "Files",
        "admins": "Admins",
        "web": "Web",
    }
    return mapping.get(mode, "Unknown")

def simulate_scan(cfg: ScanConfig) -> dict:
    time.sleep(2.5)
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    return {
        "domain": cfg.domain,
        "org": "Example Corporation",
        "ctime": now_str,
        "general": {
            "robots": "✅ Found (24 rules)",
            "sitemap": "✅ Found (18 URLs)",
            "sitemap_links": 18,
            "dorking": compute_dork_mark(cfg.dorking_mode),
            "pagesearch": cfg.page_search,
            "snapshot": cfg.snapshot_mode.value.upper()
        },
        "stats": {
            "a_tsf": 14, "a_tsm": 7, "a_temails": 3, 
            "a_tips": 5, "a_tops": 8, "a_tpv": 2
        },
        "ps_stats": {
            "ps_s": 10, "ps_e": 4, "ps_f": 9, 
            "ps_c": 6, "ps_a": 2, "ps_w": 38, "ps_p": 1
        },
        "whois": {
            "domain": cfg.domain,
            "url": f"https://{cfg.domain}/",
            "ip": "104.21.56.78",
            "registrar": "Cloudflare, Inc.",
            "created": "2018-03-12 00:00:00 UTC",
            "expires": "2025-03-12 00:00:00 UTC",
            "org": cfg.domain.replace(".com", "").title() + " LLC",
            "contacts": "admin@example.com, hostmaster@cloudflare.net"
        },
        "dns_ssl": {
            "ns": "ns1.cloudflare.com, ns2.cloudflare.com",
            "mx": "mail.example.com (Priority: 10)",
            "issuer": "Let's Encrypt Authority X3",
            "subject": f"CN={cfg.domain}",
            "notBefore": "2024-01-15 00:00:00 UTC",
            "notAfter": "2025-01-15 00:00:00 UTC",
            "cn": cfg.domain,
            "serial": "03:A1:B4:C5:D6:E7:F8:9A"
        },
        "socials": {
            "Facebook": [f"https://facebook.com/{cfg.domain.replace('.com','')}", "https://fb.me/examplecorp"],
            "Twitter/X": ["https://twitter.com/examplecorp", "https://x.com/examplecorp"],
            "Instagram": [f"https://instagram.com/{cfg.domain.replace('.com','')}"],
            "Telegram": ["https://t.me/examplecorp_official"],
            "TikTok": [],
            "LinkedIn": [f"https://linkedin.com/company/{cfg.domain.replace('.com','')}"],
            "VK": [],
            "YouTube": ["https://youtube.com/@examplecorp"],
            "OK": [],
            "WeChat": []
        },
        "subdomains": [
            {"Subdomain": f"www.{cfg.domain}", "IP Address": "104.21.56.78", "Status": "✅ Active", "SSL": "🔒 Valid"},
            {"Subdomain": f"mail.{cfg.domain}", "IP Address": "104.21.56.79", "Status": "✅ Active", "SSL": "🔒 Valid"},
            {"Subdomain": f"api.{cfg.domain}", "IP Address": "104.21.56.80", "Status": "⏳ Pending", "SSL": "🔒 Valid"},
            {"Subdomain": f"dev.{cfg.domain}", "IP Address": "192.168.1.10", "Status": "❌ Inactive", "SSL": "🔓 No SSL"}
        ],
        "ips": [
            {"IP Address": "104.21.56.78", "Type": "IPv4", "Location": "🇺🇸 US, San Francisco", "ISP / ASN": "AS13335 Cloudflare"},
            {"IP Address": "104.21.56.79", "Type": "IPv4", "Location": "🇺🇸 US, Dallas", "ISP / ASN": "AS13335 Cloudflare"},
            {"IP Address": "2606:4700::6815:384e", "Type": "IPv6", "Location": "🌍 Global CDN", "ISP / ASN": "AS13335 Cloudflare"}
        ],
        "tech": {
            "Web Servers": ["nginx/1.24.0", "Apache/2.4.58"],
            "CMS": ["WordPress 6.4.2"],
            "Languages": ["PHP 8.2", "JavaScript ES6+"],
            "Frameworks": ["React 18.2", "Laravel 10.x"],
            "Analytics": ["Google Analytics 4", "Hotjar"],
            "JS Frameworks": ["jQuery 3.7.0", "Bootstrap 5.3"]
        },
        "ports": [
            {"Port": 80, "Service": "HTTP", "Category": "http", "Risk": "medium"},
            {"Port": 443, "Service": "HTTPS", "Category": "http", "Risk": "low"},
            {"Port": 22, "Service": "SSH", "Category": "ssh", "Risk": "medium"},
            {"Port": 3306, "Service": "MySQL", "Category": "database", "Risk": "high"}
        ],
        "vulns": [
            {"CVE ID": "N/A", "Description": "Missing X-Frame-Options header (Clickjacking risk)", "Severity": "medium"},
            {"CVE ID": "CVE-2023-48795", "Description": "TLS 1.0/1.1 enabled on legacy endpoint", "Severity": "high"}
        ],
        "files": {
            "robots": f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /wp-admin/",
            "sitemap": '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>https://{cfg.domain}/</loc></url>\n</urlset>'
        },
        "dorking_raw": f'site:{cfg.domain} filetype:pdf\nsite:{cfg.domain} inurl:admin\nsite:{cfg.domain} intitle:"index of"',
        "pagesearch_raw": f"Scanning {cfg.domain}...\nFound 12 email addresses.\nExtracted 8 API keys.\nDetected 3 exposed passwords.",
        "api_results": {
            "VirusTotal": '{"data":{"attributes":{"last_analysis_stats":{"malicious":0,"suspicious":1,"undetected":95}}},"meta":{"file_info":{"sha256":"a1b2c3..."}}}',
            "SecurityTrails": '{"subdomain_count": 14, "first_seen": "2018-03-12", "last_seen": "2024-05-20"}',
            "HudsonRock": '{"data":{"breaches":[{"source":"LinkedIn","date":"2023-01-15"}],"passwords":["P@ssw0rd!"]}}'
        }
    }

def apply_theme():
    st.markdown(
        """
        <style>
            /* Global Layout & Typography */
            .main > div { padding-top: 1rem; }
            h1, h2, h3, h4, h5, h6 { color: #0f172a !important; font-weight: 700 !important; margin-bottom: 0.8rem !important; line-height: 1.3 !important; }
            
            /* Section Headers */
            .stSubheader { 
                font-size: 1.25rem !important; 
                font-weight: 600 !important; 
                padding-top: 1.5rem !important; 
                border-left: 4px solid #3b82f6; 
                padding-left: 0.75rem !important;
                color: #1e293b !important;
            }
            
            /* Metrics Cards */
            div[data-testid="metric-container"] { 
                background: #ffffff !important; 
                border-radius: 12px !important; 
                padding: 1.25rem !important; 
                box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
                border: 1px solid #e2e8f0 !important;
            }
            div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; color: #64748b !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.25rem !important; }
            div[data-testid="stMetricValue"] { font-size: 1.75rem !important; font-weight: 700 !important; color: #0f172a !important; line-height: 1.2 !important; }
            
            /* Tables */
            .dataframe-table { border-collapse: collapse !important; width: 100% !important; margin-top: 0.5rem !important; }
            .dataframe-table th { background: #f8fafc !important; color: #334155 !important; font-weight: 600 !important; padding: 12px 14px !important; border-bottom: 2px solid #e2e8f0 !important; text-align: left !important; }
            .dataframe-table td { padding: 11px 14px !important; border-bottom: 1px solid #e2e8f0 !important; color: #334155 !important; font-size: 0.9rem !important; }
            .dataframe-table tr:hover { background-color: #f1f5f9 !important; }
            
            /* Expanders */
            [data-testid="stExpander"] { border-radius: 12px !important; border: 1px solid #e2e8f0 !important; margin-bottom: 1rem !important; background: #ffffff !important; }
            .streamlit-expanderHeader { font-weight: 600 !important; padding: 14px 16px !important; background: #fafbfc !important; border-radius: 12px 12px 0 0 !important; color: #334155 !important; }
            
            /* Status Badges */
            .badge { display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; margin-right: 8px; vertical-align: middle; }
            .badge-success { background: #dcfce7; color: #166534; }
            .badge-warning { background: #fef9c3; color: #854d0e; }
            .badge-danger { background: #fee2e2; color: #991b1b; }
            .badge-info { background: #dbeafe; color: #1e40af; }
            
            /* Buttons & Downloads */
            .stButton > button, .stDownloadButton > button { 
                font-weight: 600 !important; border-radius: 8px !important; padding: 0.7rem 1.2rem !important; 
                transition: all 0.2s ease !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            }
            .stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important; }
            
            /* Scrollbar */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.35); border-radius: 4px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_sidebar():
    st.sidebar.title("⚙️ Global Settings")
    with st.sidebar.expander("🔑 API Keys", expanded=False):
        st.text_input("Primary Key", type="password", key="api_key_1", placeholder="sk-...")
        st.text_input("Secondary Key", type="password", key="api_key_2", placeholder="sk-...")
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset Configuration", use_container_width=True):
        st.session_state.config = ScanConfig()
        st.session_state.scan_result = None
        st.rerun()

def render_scan_form():
    st.header("🚀 New Scan Configuration", divider="gray")
    st.caption("Configure all scan parameters below, then hit Start Scan.")
    
    col_domain, col_comment = st.columns(2)
    with col_domain:
        domain = st.text_input("Domain", value=st.session_state.config.domain, placeholder="example.com", help="Enter domain without protocol")
    with col_comment:
        comment = st.text_input("Case Comment", value=st.session_state.config.comment, placeholder="Internal note for this scan")
        
    st.markdown("---")
    st.subheader("🔎 Dorking Strategy")
    dork_labels = {"n": "None", "basic": "Basic", "iot": "IoT", "files": "Files", "admins": "Admins", "web": "Web", "custom": "Custom"}
    current_dork = st.session_state.config.dorking_mode
    selected_dork = current_dork
    dork_cols = st.columns(len(dork_labels))
    for i, (value, label) in enumerate(dork_labels.items()):
        with dork_cols[i]:
            if st.checkbox(label, value=(current_dork == value), key=f"dork_{value}"):
                selected_dork = value
    checked_dorks = [v for v in dork_labels if st.session_state.get(f"dork_{v}", False)]
    if len(checked_dorks) == 0: selected_dork = "n"
    elif len(checked_dorks) == 1: selected_dork = checked_dorks[0]
    else: selected_dork = checked_dorks[-1]
        
    st.markdown("---")
    st.subheader("📸 Snapshot Mode")
    snap_labels = {"n": "None", "s": "Screenshot", "p": "Page Copy", "w": "Wayback Machine"}
    current_snap = st.session_state.config.snapshot_mode.value if hasattr(st.session_state.config.snapshot_mode, 'value') else "n"
    selected_snap = current_snap
    snap_cols = st.columns(len(snap_labels))
    for i, (value, label) in enumerate(snap_labels.items()):
        with snap_cols[i]:
            st.checkbox(label, value=(current_snap == value), key=f"snap_{value}")
    checked_snaps = [v for v in snap_labels if st.session_state.get(f"snap_{v}", False)]
    if len(checked_snaps) == 0: selected_snap = "n"
    elif len(checked_snaps) == 1: selected_snap = checked_snaps[0]
    else: selected_snap = checked_snaps[-1]
        
    wb_from, wb_to = "", ""
    if selected_snap == "w":
        col_wb1, col_wb2 = st.columns(2)
        with col_wb1: wb_from = st.text_input("Wayback Start Date", placeholder="YYYYMMDD")
        with col_wb2: wb_to = st.text_input("Wayback End Date", placeholder="YYYYMMDD")
        
    st.markdown("---")
    st.subheader("🔍 Page Search")
    page_search = st.checkbox("Enable page search on target", value=st.session_state.config.page_search)
    keywords = []
    if page_search:
        keywords_str = st.text_input("Keywords (comma-separated)", placeholder="login, admin, dashboard, api")
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
        
    st.markdown("---")
    st.subheader("🔗 External APIs")
    api_definitions = {
        "api_vt": {"label": "VirusTotal", "id": "1"},
        "api_ss": {"label": "SecurityTrails", "id": "2"},
        "api_hb": {"label": "HudsonRock (no key)", "id": "3"}
    }
    api_col1, api_col2, api_col3 = st.columns(3)
    selected_apis = []
    for i, (key, info) in enumerate(api_definitions.items()):
        with [api_col1, api_col2, api_col3][i]:
            checked = st.checkbox(info["label"], key=key)
            if checked:
                selected_apis.append(info["id"])
                st.text_input(f"{info['label']} API Key", type="password", placeholder=f"Enter {info['label']} key...", key=f"{key}_key")
                
    st.markdown("---")
    if st.button("▶️ Start Scan", type="primary", use_container_width=True):
        if not domain or not validate_domain(domain):
            st.error("❌ Invalid domain format. Please enter a valid domain without a protocol prefix.")
            return
            
        cfg = ScanConfig(
            domain=domain, url=f"http://{domain}/", comment=comment, page_search=page_search,
            keywords=keywords, dorking_mode=selected_dork, api_ids=selected_apis if selected_apis else ["Empty"],
            snapshot_mode=SnapshotMode(selected_snap), username=None, wb_from=wb_from or "N", wb_to=wb_to or "N"
        )
        st.session_state.config = cfg
        with st.spinner("🔍 Scanning target and gathering data..."):
            try:
                result = simulate_scan(cfg)
                st.session_state.scan_result = result
                st.success(f"✅ Scan completed successfully for `{cfg.domain}`!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Scan failed: {e}")

def render_results():
    if not st.session_state.scan_result:
        st.info("👈 Configure and run a scan to see results here.")
        return
        
    res = st.session_state.scan_result
    
    st.header(f"🔍 OSINT Research Report — {res['domain']}", divider="gray")
    st.caption(res.get('org', ''))
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Robots.txt", res['general']['robots'])
        st.metric("Sitemap.xml", res['general']['sitemap'])
        st.metric("Sitemap Links", res['general']['sitemap_links'])
    with col2:
        st.metric("Google Dorking", res['general']['dorking'])
        st.metric("PageSearch", "✅ Enabled" if res['general']['pagesearch'] else "❌ Disabled")
        st.metric("Snapshotting", res['general']['snapshot'])
    with col3:
        st.metric("Report Created", res['ctime'], delta=None)
        
    st.subheader("📊 Scan Statistics")
    stats_cols = st.columns(6)
    for i, (label, val) in enumerate(res['stats'].items()):
        with stats_cols[i]:
            st.metric(label.replace('_', ' ').title(), str(val))
            
    st.subheader("🔎 PageSearch Statistics")
    ps_cols = st.columns(7)
    for i, (label, val) in enumerate(res['ps_stats'].items()):
        with ps_cols[i]:
            st.metric(label.replace('_', ' ').title(), str(val))
            
    st.subheader("🌐 Domain Information")
    w1, w2 = st.columns(2)
    with w1:
        st.markdown("**Domain:** " + res['whois']['domain'])
        st.markdown(f"**Full URL:** [{res['whois']['url']}]({res['whois']['url']})")
        st.markdown(f"**IP Address:** `{res['whois']['ip']}`")
        st.markdown("**Registrar:** " + res['whois']['registrar'])
    with w2:
        st.markdown("**Created:** " + res['whois']['created'])
        st.markdown("**Expires:** " + res['whois']['expires'])
        st.markdown("**Organization:** " + res['whois']['org'])
        st.markdown("**Contacts:** " + res['whois']['contacts'])
        
    st.subheader("🔒 DNS & SSL Information")
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**DNS Records**\n- **Name Servers:** " + res['dns_ssl']['ns'])
        st.markdown("- **MX Records:** " + res['dns_ssl']['mx'])
    with d2:
        st.markdown("**SSL Certificate**\n- **Issuer:** " + res['dns_ssl']['issuer'])
        st.markdown("- **Subject:** " + res['dns_ssl']['subject'])
        st.markdown(f"- **Valid From:** {res['dns_ssl']['notBefore']}\n- **Valid Until:** {res['dns_ssl']['notAfter']}")
        st.markdown(f"- **Common Name:** {res['dns_ssl']['cn']}\n- **Serial:** `{res['dns_ssl']['serial']}`")
        
    st.subheader("📱 Social Media Links")
    for plat, urls in res['socials'].items():
        with st.expander(f"{plat} ({len(urls)} links)", expanded=False):
            if urls:
                for url in urls:
                    st.markdown(f"- [{url}]({url})")
            else:
                st.caption("No links found.")
                
    st.subheader("🌐 Subdomains Research")
    if res['subdomains']:
        df_sub = pd.DataFrame(res['subdomains'])
        st.dataframe(df_sub, use_container_width=True, hide_index=True)
    else:
        st.info("No subdomains found.")
        
    st.subheader("🔢 IP Addresses Analysis")
    if res['ips']:
        df_ip = pd.DataFrame(res['ips'])
        st.dataframe(df_ip, use_container_width=True, hide_index=True)
    else:
        st.info("No IPs found.")
        
    st.subheader("⚙️ Technology Stack")
    tech_cols = st.columns(4)
    for i, (cat, items) in enumerate(res['tech'].items()):
        with tech_cols[i % 4]:
            st.markdown(f"**{cat}**")
            if items:
                for item in items:
                    st.caption(f"- `{item}`")
            else:
                st.caption("- None detected")
                
    tab_ports, tab_vulns = st.tabs(["🚪 Open Ports", "⚠️ Vulnerabilities"])
    with tab_ports:
        if res['ports']:
            df_ports = pd.DataFrame(res['ports'])
            st.dataframe(df_ports, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No open ports detected.")
            
    with tab_vulns:
        if res['vulns']:
            df_vuln = pd.DataFrame(res['vulns'])
            st.dataframe(df_vuln, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No vulnerabilities detected.")
            
    with st.expander("📄 Technical Files (robots.txt / sitemap.xml)", expanded=False):
        st.code(res['files']['robots'], language="text")
        st.divider()
        st.code(res['files']['sitemap'], language="xml")
        
    if res.get('dorking_raw'):
        with st.expander("🔍 Dorking Scan Results", expanded=False):
            st.text_area("Google Dorking Output", value=res['dorking_raw'], height=200)
            
    if res.get('pagesearch_raw'):
        with st.expander("📑 PageSearch Results", expanded=False):
            st.text_area("PageSearch Process Listing", value=res['pagesearch_raw'], height=200)
            
    for api_name, content in res['api_results'].items():
        if content:
            with st.expander(f"🔗 {api_name} API Results", expanded=False):
                st.code(content, language="json")
                
    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_data = json.dumps(res, indent=2)
        st.download_button("📥 Download Full JSON Report", data=csv_data, file_name=f"dpulse_report_{res['domain'].replace('.', '_')}.json", mime="application/json")
    with col_dl2:
        summary = f"Domain,Status,Created\n{res['domain']},Success,{res['ctime']}\n"
        st.download_button("📥 Download Summary CSV", data=summary, file_name="dpulse_summary.csv", mime="text/csv")
        
    st.caption("Created with DPULSE by OSINT-TECHNOLOGIES | [GitHub](https://github.com/OSINT-TECHNOLOGIES) | [PyPI](https://pypi.org/project/dpulse/)")

def main():
    st.set_page_config(page_title="DPULSE Web", page_icon="🌐", layout="wide")
    apply_theme()
    render_sidebar()
    
    tab1, tab2 = st.tabs(["🚀 New Scan", "📊 Results"])
    with tab1:
        render_scan_form()
    with tab2:
        render_results()

if __name__ == "__main__":
    main()
