import sys
import os
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import re
import time
import webbrowser
import streamlit as st

def setup_paths():
    base = os.path.dirname(os.path.abspath(__file__))
    sys.path.extend([base, f"{base}/service", f"{base}/pagesearch", 
                     f"{base}/dorking", f"{base}/snapshotting"])

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
if "is_scanning" not in st.session_state:
    st.session_state.is_scanning = False

def validate_domain(domain: str) -> bool:
    pattern = r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain))

def compute_dork_mark(mode: str) -> str:
    if mode == "n": return "No dorking"
    if mode.startswith("custom+"): return f"Custom ({mode.split('+')[1]})"
    mapping = {"basic": "Basic", "iot": "IoT", "files": "Files", "admins": "Admins", "web": "Web"}
    return mapping.get(mode, "Unknown")

def perform_real_scan(cfg: ScanConfig) -> dict:
    setup_paths() 
    
    short_domain = cfg.domain.replace(".", "")
    url = f"http://{cfg.domain}/"
    
    pagesearch_flag = "y" if cfg.page_search else "n"
    keywords_str = ",".join(cfg.keywords) if cfg.keywords else ""
    dorking_flag = cfg.dorking_mode.lower()
    used_api_flag = [x.strip() for x in cfg.api_ids] if cfg.api_ids[0] != "Empty" else ["Empty"]
    snapshotting_flag = cfg.snapshot_mode.value
    
    dp = DataProcessing()
    data_array, report_info_array = dp.data_gathering(
        short_domain=short_domain, url=url, report_file_type="html",
        pagesearch_flag=pagesearch_flag, keywords=keywords_str, keywords_flag="",
        dorking_flag=dorking_flag, used_api_flag=used_api_flag,
        snapshotting_flag=snapshotting_flag, username=cfg.username,
        from_date=cfg.wb_from if cfg.snapshot_mode == SnapshotMode.WAYBACK else "N",
        end_date=cfg.wb_to if cfg.snapshot_mode == SnapshotMode.WAYBACK else "N"
    )

    ip = data_array[0]
    res = data_array[1]
    mails = data_array[2]
    subdomains = data_array[3]
    subdomains_amount = data_array[4]
    social_medias = data_array[5]
    subdomain_mails = data_array[6]
    subdomain_ip = data_array[8]
    issuer = data_array[9]
    subject = data_array[10]
    notBefore = data_array[11]
    notAfter = data_array[12]
    commonName = data_array[13]
    serialNumber = data_array[14]
    mx_records = data_array[15]
    robots_txt_result = data_array[16]
    sitemap_xml_result = data_array[17]
    sitemap_links_status = data_array[18]
    web_servers = data_array[19]
    cms = data_array[20]
    programming_languages = data_array[21]
    web_frameworks = data_array[22]
    analytics = data_array[23]
    javascript_frameworks = data_array[24]
    ports = data_array[25]
    hostnames = data_array[26]
    cpes = data_array[27]
    tags = data_array[28]
    vulns = data_array[29]
    common_socials = data_array[30]
    total_socials = data_array[31]
    ps_emails_return = data_array[32]
    accessible_subdomains = data_array[33]
    emails_amount = data_array[34]
    files_counter = data_array[35]
    cookies_counter = data_array[36]
    api_keys_counter = data_array[37]
    website_elements_counter = data_array[38]
    exposed_passwords_counter = data_array[39]
    total_links_counter = data_array[40]
    accessed_links_counter = data_array[41]
    keywords_messages_list = data_array[42]
    dorking_status = data_array[43]
    dorking_file_path = data_array[44]
    virustotal_output = data_array[45]
    securitytrails_output = data_array[46]
    hudsonrock_output = data_array[47]
    ps_string = data_array[48]
    total_ports = data_array[49]
    total_ips = data_array[50]
    total_vulns = data_array[51]

    casename = report_info_array[0]
    db_casename = report_info_array[1]
    db_creation_date = report_info_array[2]
    report_folder = report_info_array[3]
    ctime = report_info_array[4]
    report_file_type = report_info_array[5]
    report_ctime = report_info_array[6]
    api_scan_db = report_info_array[7]
    used_api_flag_out = report_info_array[8]

    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader('.'))
    template_path = 'service//pdf_report_templates//modern_report_template.html'
    try:
        template = env.get_template(template_path)
        html_output = template.render({
            "sh_domain": short_domain, "full_url": url, "ip_address": ip,
            "registrar": res["registrar"], "creation_date": res["creation_date"],
            "expiration_date": res["expiration_date"], "name_servers": ", ".join(res["name_servers"]),
            "org": res["org"], "mails": mails, "subdomain_mails": subdomain_mails,
            "subdomain_socials": social_medias, "subdomain_ip": subdomain_ip,
            "subdomains": subdomains, "fb_links": common_socials.get("Facebook", []),
            "tw_links": common_socials.get("Twitter", []), "inst_links": common_socials.get("Instagram", []),
            "tg_links": common_socials.get("Telegram", []), "tt_links": common_socials.get("TikTok", []),
            "li_links": common_socials.get("LinkedIn", []), "vk_links": common_socials.get("VKontakte", []),
            "yt_links": common_socials.get("YouTube", []), "wc_links": common_socials.get("WeChat", []),
            "ok_links": common_socials.get("Odnoklassniki", []), "xcom_links": common_socials.get("X.com", []),
            "robots_txt_result": robots_txt_result, "sitemap_xml_result": sitemap_xml_result,
            "sitemap_links": sitemap_links_status, "web_servers": web_servers, "cms": cms,
            "programming_languages": programming_languages, "ip_addresses": list(subdomain_ip) + [ip],
            "javascript_frameworks": javascript_frameworks, "ctime": report_ctime,
            "a_tsf": subdomains_amount, "mx_records": mx_records, "issuer": issuer,
            "subject": subject, "notBefore": notBefore, "notAfter": notAfter,
            "commonName": commonName, "serialNumber": serialNumber, "ports": ports,
            "hostnames": hostnames, "cpes": cpes, "tags": tags, "vulns": vulns,
            "a_tsm": total_socials, "pagesearch_ui_mark": pagesearch_flag == "y",
            "dorking_status": dorking_status,
            "add_dsi": "", "ps_s": accessible_subdomains, "ps_e": emails_amount,
            "ps_f": files_counter, "ps_c": cookies_counter, "ps_a": api_keys_counter,
            "ps_w": website_elements_counter, "ps_p": exposed_passwords_counter,
            "ss_l": total_links_counter, "ss_a": accessed_links_counter,
            "hudsonrock_output": hudsonrock_output, "snapshotting_ui_mark": snapshotting_flag in ['s','p','w'],
            "virustotal_output": virustotal_output, "securitytrails_output": securitytrails_output,
            "ps_string": ps_string, "a_tops": total_ports, "a_temails": len(mails),
            "a_tips": total_ips, "a_tpv": total_vulns,
            "robots_content": "", "sitemap_xml_content": "", "sitemap_txt_content": ""
        })
    except Exception as e:
        html_output = f"<div style='color:red;padding:20px;'>Template error: {e}</div>"

    return {
        "status": "success",
        "domain": cfg.domain,
        "report_type": cfg.report_type.value.upper(),
        "dorking": compute_dork_mark(cfg.dorking_mode),
        "apis": ", ".join(used_api_flag_out) if used_api_flag_out[0] != "Empty" else "None",
        "snapshot": cfg.snapshot_mode.value,
        "duration": "~2.5s",
        "html_content": html_output
    }

def render_sidebar():
    st.sidebar.title("⚙️ Global Settings")
    with st.sidebar.expander("🔑 API Keys", expanded=False):
        st.text_input("Primary Key", type="password", key="api_key_1", placeholder="sk-...")
        st.text_input("Secondary Key", type="password", key="api_key_2", placeholder="sk-...")
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset Configuration"):
        st.session_state.config = ScanConfig()
        st.session_state.scan_result = None
        st.rerun()

def render_scan_form():
    st.header("🚀 New Scan Configuration")
    st.caption("Configure target, dorking strategy, APIs and snapshots. All data stays in session.")
    with st.form("scan_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            domain = st.text_input(
                "Target Domain",
                value=st.session_state.config.domain,
                help="e.g., example.com (no http/https)"
            )
            comment = st.text_input("Case Comment / Internal Note", value=st.session_state.config.comment)
        with col2:
            report_type = st.selectbox(
                "Report Format",
                [rt.value for rt in ReportType],
                index=0,
                help="Currently only HTML is supported"
            )
            page_search = st.checkbox("Enable Page Search", value=st.session_state.config.page_search)
        if page_search:
            keywords_str = st.text_input(
                "Keywords (comma-separated)",
                placeholder="login, admin, dashboard, api",
                help="Leave empty to search all pages"
            )
            st.session_state.config.keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
        dorking_mode = st.selectbox(
            "Dorking Strategy",
            ["None", "Basic", "IoT", "Files", "Admins", "Web", "Custom"],
            index=["n", "basic", "iot", "files", "admins", "web", "custom"].index(
                st.session_state.config.dorking_mode) if st.session_state.config.dorking_mode != "n" else 0,
            help="Select predefined or custom dork sets"
        )
        col3, col4 = st.columns(2)
        with col3:
            use_api = st.checkbox("Use External APIs", value=st.session_state.config.api_ids[0] != "Empty")
            api_input = ""
            username = None
            if use_api:
                api_input = st.text_input("API IDs (comma-separated)", placeholder="1, 3",
                                          help="Check your API manager for valid IDs")
                if '3' in api_input.split(","):
                    username = st.text_input("Known Username from domain (optional)")
        with col4:
            snap_mode = st.selectbox(
                "Snapshot Mode",
                ["None", "Screenshot", "Page Copy", "Wayback Machine"],
                index=["n", "s", "p", "w"].index(
                    st.session_state.config.snapshot_mode.value) if st.session_state.config.snapshot_mode != SnapshotMode.NONE else 0,
                help="Capture visual or HTML state of the target"
            )
            wb_from, wb_to = "", ""
            if snap_mode == "Wayback Machine":
                col_w1, col_w2 = st.columns(2)
                with col_w1: wb_from = st.text_input("Start (YYYYMMDD)")
                with col_w2: wb_to = st.text_input("End (YYYYMMDD)")
        submitted = st.form_submit_button("▶️ Start Scan", type="primary")
    if submitted:
        if not domain or not validate_domain(domain):
            st.error("❌ Invalid domain format. Please enter a valid domain without protocol.")
            return
        cfg = ScanConfig(
            domain=domain, url=f"http://{domain}/", comment=comment,
            report_type=ReportType(report_type), page_search=page_search,
            keywords=st.session_state.config.keywords, dorking_mode=dorking_mode.lower(),
            api_ids=[x.strip() for x in api_input.split(",") if x.strip().isdigit()] if use_api and api_input else [
                "Empty"],
            snapshot_mode=SnapshotMode(snap_mode[0].lower()), username=username,
            wb_from=wb_from or "N", wb_to=wb_to or "N"
        )
        st.session_state.config = cfg
        with st.spinner("🔍 Scanning target and gathering data..."):
            try:
                result = perform_real_scan(cfg)
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
    st.header("📊 Scan Results")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Target", res["domain"])
    with col2: st.metric("Duration", res["duration"])
    with col3: st.metric("Status", "✅ Success")
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
        type="primary"
    )

def main():
    st.set_page_config(page_title="DPULSE Web", page_icon="🌐", layout="wide")
    st.markdown("""
        <style>
            .main > div { padding-top: 1.5rem; }
            .stButton > button { width: 100%; font-weight: 600; border-radius: 8px; }
            .css-1r6slb0, .css-1e4ez7s { border-radius: 12px !important; }
            section[data-testid="stSidebar"] { background-color: #f8f9fa; }
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
