import streamlit as st
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import re
import time


class ReportType(str, Enum):
    HTML = "html"

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
    report_type: ReportType = ReportType.HTML
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
    if mode == "n": return "No dorking"
    if mode.startswith("custom+"): return f"Custom ({mode.split('+')[1]})"
    mapping = {"basic": "Basic", "iot": "IoT", "files": "Files", "admins": "Admins", "web": "Web"}
    return mapping.get(mode, "Unknown")

def simulate_scan(cfg: ScanConfig) -> dict:
    """Backend-заглушка. Замените на реальный вызов data_processing.data_gathering()"""
    time.sleep(2.5)  
    return {
        "status": "success",
        "domain": cfg.domain,
        "report_type": cfg.report_type.value.upper(),
        "dorking": compute_dork_mark(cfg.dorking_mode),
        "apis": ", ".join(cfg.api_ids) if cfg.api_ids[0] != "Empty" else "None",
        "snapshot": cfg.snapshot_mode.value,
        "duration": "~2.5s",
        "html_content": f"""
            <div style="padding: 24px; font-family: system-ui, sans-serif;">
                <h1 style="margin:0 0 8px 0; color:#0f172a;">📊 DPULSE Report</h1>
                <p style="color:#64748b; margin-bottom:16px;"><strong>Target:</strong> {cfg.domain}</p>
                <hr style="border:none; border-top:1px solid #e2e8f0; margin: 16px 0;">
                <div style="display:flex; gap:12px; flex-wrap:wrap;">
                    <span style="background:#f1f5f9; padding:4px 10px; border-radius:6px; font-size:13px; color:#334155;">Type: {cfg.report_type.value.upper()}</span>
                    <span style="background:#f1f5f9; padding:4px 10px; border-radius:6px; font-size:13px; color:#334155;">Dorking: {compute_dork_mark(cfg.dorking_mode)}</span>
                </div>
                <p style="color: #16a34a; margin-top: 20px; font-weight: 500;">✅ Scan completed successfully.</p>
            </div>
        """
    }


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
    st.caption("Configure target, dorking strategy, APIs and snapshots. All data stays in session.")

    dork_options = ["None", "Basic", "IoT", "Files", "Admins", "Web", "Custom"]
    dork_values = ["n", "basic", "iot", "files", "admins", "web", "custom"]
    current_dork = st.session_state.config.dorking_mode
    try:
        dork_idx = dork_values.index(current_dork)
    except ValueError:
        dork_idx = 0

    snap_options = ["None", "Screenshot", "Page Copy", "Wayback Machine"]
    snap_values = ["n", "s", "p", "w"]
    current_snap_val = st.session_state.config.snapshot_mode.value if hasattr(st.session_state.config.snapshot_mode, 'value') else "n"
    try:
        snap_idx = snap_values.index(current_snap_val)
    except ValueError:
        snap_idx = 0

    with st.form("scan_form", border=False):
        col1, col2 = st.columns(2)
        
        with col1:
            domain = st.text_input("Target Domain", value=st.session_state.config.domain, help="e.g., example.com")
            comment = st.text_input("Case Comment / Internal Note", value=st.session_state.config.comment)

        with col2:
            report_type = st.selectbox("Report Format", [rt.value for rt in ReportType], index=0, help="Currently only HTML is supported")
            page_search = st.checkbox("Enable Page Search", value=st.session_state.config.page_search)

        if page_search:
            keywords_str = st.text_input(
                "Keywords (comma-separated)",
                placeholder="login, admin, dashboard, api",
                help="Leave empty to search all pages"
            )
            st.session_state.config.keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

        dorking_mode = st.selectbox("Dorking Strategy", dork_options, index=dork_idx, help="Select predefined or custom dork sets")

        col3, col4 = st.columns(2)
        
        with col3:
            use_api = st.checkbox("Use External APIs", value=st.session_state.config.api_ids[0] != "Empty")
            api_input = ""
            username = None
            if use_api:
                api_input = st.text_input("API IDs (comma-separated)", placeholder="1, 3", help="Check your API manager for valid IDs")
                if '3' in api_input.split(","):
                    username = st.text_input("Known Username from domain (optional)")

        with col4:
            snap_mode = st.selectbox("Snapshot Mode", snap_options, index=snap_idx, help="Capture visual or HTML state of the target")
            wb_from, wb_to = "", ""
            if snap_mode == "Wayback Machine":
                c1, c2 = st.columns(2)
                with c1: wb_from = st.text_input("Start (YYYYMMDD)")
                with c2: wb_to = st.text_input("End (YYYYMMDD)")

        submitted = st.form_submit_button("▶️ Start Scan", type="primary")

    if submitted:
        if not domain or not validate_domain(domain):
            st.error("❌ Invalid domain format. Please enter a valid domain without protocol.")
            return

        cfg = ScanConfig(
            domain=domain, url=f"http://{domain}/", comment=comment,
            report_type=ReportType(report_type), page_search=page_search,
            keywords=st.session_state.config.keywords, dorking_mode=dorking_mode.lower(),
            api_ids=[x.strip() for x in api_input.split(",") if x.strip().isdigit()] if use_api and api_input else ["Empty"],
            snapshot_mode=SnapshotMode(snap_mode[0].lower()), username=username,
            wb_from=wb_from or "N", wb_to=wb_to or "N"
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
    
    st.header("📊 Scan Results", divider="gray")
    
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.metric("Target", res["domain"])
    with col2: 
        st.metric("Duration", res["duration"])
    with col3: 
        st.metric("Status", "✅ Success")

    st.markdown("---")
    
    with st.expander("📋 Configuration Summary"):
        st.json({
            "Report Type": res["report_type"],
            "Dorking Strategy": res["dorking"],
            "APIs Used": res["apis"],
            "Snapshot Mode": res["snapshot"]
        })

    with st.expander("📄 Generated Report (HTML Preview)"):
        st.markdown(res["html_content"], unsafe_allow_html=True)

    st.download_button(
        label="⬇️ Download HTML Report",
        data=res["html_content"],
        file_name=f"dpulse_report_{res['domain'].replace('.', '_')}.html",
        mime="text/html",
        type="primary",
        use_container_width=True
    )


def main():
    st.set_page_config(page_title="DPULSE Web", page_icon="🌐", layout="wide")
    st.markdown("""
        <style>
            /* Base & Layout */
            .main { background-color: #ffffff; }
            
            /* Dark Sidebar Styling */
            section[data-testid="stSidebar"] { 
                background-color: #0f172a !important; 
                color: #e2e8f0 !important; 
                border-right: 1px solid #1e293b !important;
            }
            section[data-testid="stSidebar"] h1, 
            section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] p, 
            section[data-testid="stSidebar"] label { color: #e2e8f0 !important; }
            
            /* Sidebar Inputs & Selects */
            section[data-testid="stSidebar"] .stTextInput > div > div > input, 
            section[data-testid="stSidebar"] .stSelectbox > div > div > select,
            section[data-testid="stSidebar"] .stNumberInput > div > div > input { 
                background-color: #1e293b !important; 
                color: #ffffff !important; 
                border: 1px solid #334155 !important; 
                border-radius: 6px !important;
            }
            section[data-testid="stSidebar"] .stCheckbox label { color: #e2e8f0 !important; }
            
            /* Main Content Typography */
            h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.02em; color: #0f172a !important; margin-bottom: 0.5rem !important; }
            .stTabs [data-baseweb="tab-list"] { gap: 8px; }
            .stTabs [data-baseweb="tab"] { 
                height: 48px; white-space: pre-wrap; background-color: #f1f5f9 !important; 
                border-radius: 8px !important; padding: 0.5rem 1rem !important; font-weight: 500 !important; color: #64748b !important;
            }
            .stTabs [aria-selected="true"] { background-color: #ffffff !important; border-bottom: 2px solid #3b82f6 !important; color: #0f172a !important; }
            
            /* Buttons & Cards */
            .stButton > button { width: 100%; font-weight: 500; border-radius: 8px; padding: 0.6rem 1rem; transition: all 0.2s ease; }
            .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
            
            /* Metrics & Expanders */
            div[data-testid="metric-container"] { background-color: #f8fafc; border-radius: 8px; padding: 1rem !important; border: 1px solid #e2e8f0; }
            .stExpander { border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff; }
        </style>
    """, unsafe_allow_html=True)

    render_sidebar()
    
    tab1, tab2 = st.tabs(["🚀 New Scan", "📊 Results"])
    
    with tab1:
        render_scan_form()
        
    with tab2:
        render_results()

if __name__ == "__main__":
    main()
