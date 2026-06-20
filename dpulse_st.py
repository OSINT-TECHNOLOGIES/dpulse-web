import streamlit as st
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import re
import time
import os


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


def load_report_html() -> str:
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "report.html"
    )
    if not os.path.exists(template_path):
        return "<p>&#10060; <b>report.html</b> not found next to the application file.</p>"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def simulate_scan(cfg: ScanConfig) -> dict:
    time.sleep(2.5)
    html_content = load_report_html()
    return {
        "status": "success",
        "domain": cfg.domain,
        "dorking": compute_dork_mark(cfg.dorking_mode),
        "apis": ", ".join(cfg.api_ids) if cfg.api_ids[0] != "Empty" else "None",
        "snapshot": cfg.snapshot_mode.value,
        "duration": "~2.5s",
        "html_content": html_content,
    }


def apply_theme():
    st.markdown(
        """
        <style>
            /* ===== Tabs ===== */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 48px;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-weight: 500;
            }

            /* ===== Buttons ===== */
            .stButton > button,
            .stDownloadButton > button {
                font-weight: 500;
                border-radius: 8px;
                padding: 0.6rem 1rem;
                transition: all 0.2s ease;
            }
            .stButton > button:hover,
            .stDownloadButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15);
            }

            /* ===== Metrics ===== */
            div[data-testid="metric-container"] {
                border-radius: 8px;
                padding: 1rem;
            }

            /* ===== Expander ===== */
            .stExpander {
                border-radius: 8px;
            }

            /* ===== Form — remove border ===== */
            [data-testid="stForm"] {
                border: none !important;
                padding: 0 !important;
            }

            /* ===== Neutral scrollbar ===== */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb {
                background: rgba(128, 128, 128, 0.35);
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(128, 128, 128, 0.55);
            }
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
    current_snap_val = (
        st.session_state.config.snapshot_mode.value
        if hasattr(st.session_state.config.snapshot_mode, "value")
        else "n"
    )
    try:
        snap_idx = snap_values.index(current_snap_val)
    except ValueError:
        snap_idx = 0

    with st.form("scan_form", border=False):
        col1, col2 = st.columns(2)

        with col1:
            domain = st.text_input(
                "Target Domain",
                value=st.session_state.config.domain,
                help="e.g., example.com",
            )
        with col2:
            comment = st.text_input(
                "Case Comment / Internal Note",
                value=st.session_state.config.comment,
            )

        page_search = st.checkbox(
            "Enable Page Search", value=st.session_state.config.page_search
        )

        if page_search:
            keywords_str = st.text_input(
                "Keywords (comma-separated)",
                placeholder="login, admin, dashboard, api",
                help="Leave empty to search all pages",
            )
            st.session_state.config.keywords = [
                k.strip() for k in keywords_str.split(",") if k.strip()
            ]

        dorking_mode = st.selectbox(
            "Dorking Strategy",
            dork_options,
            index=dork_idx,
            help="Select predefined or custom dork sets",
        )

        col3, col4 = st.columns(2)

        with col3:
            use_api = st.checkbox(
                "Use External APIs",
                value=st.session_state.config.api_ids[0] != "Empty",
            )
            api_input = ""
            username = None
            if use_api:
                api_input = st.text_input(
                    "API IDs (comma-separated)",
                    placeholder="1, 3",
                    help="Check your API manager for valid IDs",
                )
                if "3" in api_input.split(","):
                    username = st.text_input(
                        "Known username from domain (optional)"
                    )

        with col4:
            snap_mode = st.selectbox(
                "Snapshot Mode",
                snap_options,
                index=snap_idx,
                help="Capture visual or HTML state of the target",
            )
            wb_from, wb_to = "", ""
            if snap_mode == "Wayback Machine":
                c1, c2 = st.columns(2)
                with c1:
                    wb_from = st.text_input("Start date (YYYYMMDD)")
                with c2:
                    wb_to = st.text_input("End date (YYYYMMDD)")

        submitted = st.form_submit_button("▶️ Start Scan", type="primary")

    if submitted:
        if not domain or not validate_domain(domain):
            st.error(
                "❌ Invalid domain format. Please enter a valid domain without a protocol prefix."
            )
            return

        cfg = ScanConfig(
            domain=domain,
            url=f"http://{domain}/",
            comment=comment,
            page_search=page_search,
            keywords=st.session_state.config.keywords,
            dorking_mode=dorking_mode.lower(),
            api_ids=(
                [x.strip() for x in api_input.split(",") if x.strip().isdigit()]
                if use_api and api_input
                else ["Empty"]
            ),
            snapshot_mode=SnapshotMode(snap_mode[0].lower()),
            username=username,
            wb_from=wb_from or "N",
            wb_to=wb_to or "N",
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
        st.json(
            {
                "Report Type": "HTML",
                "Dorking Strategy": res["dorking"],
                "APIs Used": res["apis"],
                "Snapshot Mode": res["snapshot"],
            }
        )

    with st.expander("📄 Generated Report (HTML Preview)", expanded=True):
        st.components.v1.html(res["html_content"], height=600, scrolling=True)

    st.download_button(
        label="⬇️ Download HTML Report",
        data=res["html_content"],
        file_name=f"dpulse_report_{res['domain'].replace('.', '_')}.html",
        mime="text/html",
        type="primary",
        use_container_width=True,
    )


def main():
    st.set_page_config(
        page_title="DPULSE Web",
        page_icon="🌐",
        layout="wide",
    )
    apply_theme()
    render_sidebar()

    tab1, tab2 = st.tabs(["🚀 New Scan", "📊 Results"])

    with tab1:
        render_scan_form()
    with tab2:
        render_results()


if __name__ == "__main__":
    main()
