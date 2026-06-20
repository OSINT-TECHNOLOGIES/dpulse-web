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
            .stTabs [data-baseweb="tab-list"] { gap: 8px; }
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

            /* ===== Form — remove border ===== */
            [data-testid="stForm"] {
                border: none !important;
                padding: 0 !important;
            }

            /* ===== Report iframe ===== */
            .report-frame iframe {
                width: 100% !important;
                min-height: 80vh !important;
                border: none !important;
                border-radius: 8px;
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
    st.caption("Configure all scan parameters below, then hit Start Scan.")


    st.subheader("🎯 Target Information")

    col_domain, col_comment = st.columns(2)
    with col_domain:
        domain = st.text_input(
            "Domain",
            value=st.session_state.config.domain,
            placeholder="example.com",
            help="Enter domain without protocol (http/https)",
        )
    with col_comment:
        comment = st.text_input(
            "Case Comment",
            value=st.session_state.config.comment,
            placeholder="Internal note for this scan",
        )

    st.markdown("---")


    st.subheader("🔎 Dorking Strategy")
    st.caption("Select one dorking mode. Only one option can be active at a time.")

    dork_labels = {
        "n": "None",
        "basic": "Basic",
        "iot": "IoT",
        "files": "Files",
        "admins": "Admins",
        "web": "Web",
        "custom": "Custom",
    }
    current_dork = st.session_state.config.dorking_mode

    dork_cols = st.columns(len(dork_labels))
    selected_dork = current_dork

    for i, (value, label) in enumerate(dork_labels.items()):
        with dork_cols[i]:
            if st.checkbox(
                label,
                value=(current_dork == value),
                key=f"dork_{value}",
            ):
                selected_dork = value

    checked_dorks = [v for v in dork_labels if st.session_state.get(f"dork_{v}", False)]
    if len(checked_dorks) == 0:
        selected_dork = "n"
    elif len(checked_dorks) == 1:
        selected_dork = checked_dorks[0]
    else:
        new_picks = [v for v in checked_dorks if v != current_dork]
        selected_dork = new_picks[-1] if new_picks else checked_dorks[-1]

    st.markdown("---")


    st.subheader("📸 Snapshot Mode")
    st.caption("Select one snapshot method. Only one option can be active at a time.")

    snap_labels = {
        "n": "None",
        "s": "Screenshot",
        "p": "Page Copy",
        "w": "Wayback Machine",
    }
    current_snap = (
        st.session_state.config.snapshot_mode.value
        if hasattr(st.session_state.config.snapshot_mode, "value")
        else "n"
    )

    snap_cols = st.columns(len(snap_labels))
    selected_snap = current_snap

    for i, (value, label) in enumerate(snap_labels.items()):
        with snap_cols[i]:
            st.checkbox(
                label,
                value=(current_snap == value),
                key=f"snap_{value}",
            )

    checked_snaps = [v for v in snap_labels if st.session_state.get(f"snap_{v}", False)]
    if len(checked_snaps) == 0:
        selected_snap = "n"
    elif len(checked_snaps) == 1:
        selected_snap = checked_snaps[0]
    else:
        new_picks = [v for v in checked_snaps if v != current_snap]
        selected_snap = new_picks[-1] if new_picks else checked_snaps[-1]

    wb_from, wb_to = "", ""
    if selected_snap == "w":
        col_wb1, col_wb2 = st.columns(2)
        with col_wb1:
            wb_from = st.text_input("Wayback Start Date", placeholder="YYYYMMDD")
        with col_wb2:
            wb_to = st.text_input("Wayback End Date", placeholder="YYYYMMDD")

    st.markdown("---")


    st.subheader("🔍 Page Search")

    page_search = st.checkbox(
        "Enable page search on target",
        value=st.session_state.config.page_search,
    )

    keywords = []
    if page_search:
        keywords_str = st.text_input(
            "Keywords (comma-separated)",
            placeholder="login, admin, dashboard, api",
            help="Leave empty to search all pages",
        )
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

    st.markdown("---")


    st.subheader("🔗 External APIs")
    st.caption("Check each API you want to use. A key input field will appear for each selected API.")

    api_definitions = {
        "api_vt": {"label": "VirusTotal", "id": "1"},
        "api_ss": {"label": "SecurityTrails", "id": "2"},
        "api_hb": {"label": "HudsonRock (doesn't require API key)", "id": "3"},
    }

    api_col1, api_col2, api_col3 = st.columns(3)
    api_containers = [api_col1, api_col2, api_col3]

    selected_apis = []
    api_keys_entered = {}
    username = None

    for i, (key, info) in enumerate(api_definitions.items()):
        with api_containers[i]:
            checked = st.checkbox(info["label"], key=key)
            if checked:
                selected_apis.append(info["id"])
                api_key_val = st.text_input(
                    f"{info['label']} API Key",
                    type="password",
                    placeholder=f"Enter {info['label']} key...",
                    key=f"{key}_key",
                )
                api_keys_entered[info["id"]] = api_key_val


    st.markdown("---")


    if st.button("▶️ Start Scan", type="primary", use_container_width=True):
        if not domain or not validate_domain(domain):
            st.error("❌ Invalid domain format. Please enter a valid domain without a protocol prefix.")
            return

        cfg = ScanConfig(
            domain=domain,
            url=f"http://{domain}/",
            comment=comment,
            page_search=page_search,
            keywords=keywords,
            dorking_mode=selected_dork,
            api_ids=selected_apis if selected_apis else ["Empty"],
            snapshot_mode=SnapshotMode(selected_snap),
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

    st.subheader("📄 Interactive Report")

    st.markdown('<div class="report-frame">', unsafe_allow_html=True)
    st.components.v1.html(res["html_content"], height=800, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

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
