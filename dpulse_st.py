import sys
import os
import re
import shutil
import webbrowser
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import Callable, Dict, List, Optional
from colorama import Fore, Style
from rich.console import Console
import streamlit as st

sys.path.append('datagather_modules')
sys.path.append('service')
sys.path.append('reporting_modules')
sys.path.append('dorking')
sys.path.append('apis')
sys.path.append('snapshotting')

from config_processing import create_config, check_cfg_presence, read_config, print_and_return_config
import db_processing as db
import cli_init
from dorking_handler import dorks_files_check
from data_assembler import DataProcessing
from logs_processing import logging
from db_creator import get_columns_amount, manage_dorks
from misc import domain_precheck, time_processing

console = Console()
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'service' / 'config.ini'
DORKING_DIR = BASE_DIR / 'dorking'
APIS_DIR = BASE_DIR / 'apis'

data_processing = DataProcessing()
cli = cli_init.Menu()


class ReportType(str, Enum):
    HTML = "html"


class SnapshotMode(str, Enum):
    NONE = "n"
    SCREENSHOT = "s"
    PAGE_COPY = "p"
    WAYBACK = "w"


@dataclass
class ScanOptions:
    short_domain: str
    url: str
    case_comment: str
    report_type: ReportType
    page_search: bool
    keywords: Optional[List[str]]
    dorking_flag: str
    used_api_ids: List[str]
    snapshot_mode: SnapshotMode
    username: Optional[str] = None
    wb_from: str = 'N'
    wb_to: str = 'N'
    pagesearch_ui_mark: str = "No"
    snapshotting_ui_mark: str = "No"


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"y", "yes", "да", "si", "1", "true", "t"}


def is_valid_domain(domain: str) -> bool:
    pattern = r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain))


def validate_yyyymmdd(s: str) -> bool:
    return bool(re.fullmatch(r"\d{8}", s))


def sanitize_db_filename(name: str) -> str:
    safe = os.path.basename(name).split('.')[0]
    if not re.fullmatch(r"[a-zA-Z0-9_\-]{1,50}", safe):
        raise ValueError("Invalid DB name")
    return safe


def compute_dorking_ui_mark(dorking_flag: str) -> str:
    try:
        if dorking_flag == 'n':
            return 'No'
        if dorking_flag.startswith('custom+'):
            db_name = dorking_flag.split('+', 1)[1]
            rc = get_columns_amount(str(DORKING_DIR / db_name), 'dorks')
            return f'Yes, Custom table dorking ({rc} dorks)'

        mapping = {
            'basic': 'basic_dorking.db',
            'iot': 'iot_dorking.db',
            'files': 'files_dorking.db',
            'admins': 'adminpanels_dorking.db',
            'web': 'webstructure_dorking.db'
        }
        if dorking_flag in mapping:
            db_name = mapping[dorking_flag]
            table = f'{dorking_flag}_dorks'
            rc = get_columns_amount(str(DORKING_DIR / db_name), table)
            return f'Yes, {dorking_flag} dorking ({rc} dorks)'
    except Exception as e:
        logging.error("Failed to compute dorking UI mark: %s", e, exc_info=True)
        return 'Dorking info unavailable'
    return 'No'


def process_report(options: ScanOptions):
    import html_report_creation as html_rc
    with console.status("[magenta]Processing scan...[/magenta]", spinner="dots"):
        start = perf_counter()
        pagesearch_flag_str = 'y' if options.page_search else 'n'
        keywords_flag = 1 if (options.page_search and options.keywords and len(options.keywords) > 0) else 0
        keywords_payload = options.keywords if options.page_search else ''

        data_array, report_info_array = data_processing.data_gathering(
            options.short_domain,
            options.url,
            options.report_type.value,
            pagesearch_flag_str,
            keywords_payload,
            keywords_flag,
            options.dorking_flag,
            options.used_api_ids if options.used_api_ids else ['Empty'],
            options.snapshot_mode.value,
            options.username,
            options.wb_from,
            options.wb_to
        )
        end_time_str = time_processing(perf_counter() - start)

    if options.report_type == ReportType.HTML:
        html_rc.report_assembling(
            options.short_domain, options.url, options.case_comment,
            data_array, report_info_array,
            options.pagesearch_ui_mark, end_time_str, options.snapshotting_ui_mark
        )


def handle_scan():
    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            short_domain = st.text_input("Target domain name", placeholder="example.com")

            if not short_domain or not is_valid_domain(short_domain):
                st.error("Please enter a valid domain name (e.g., example.com)")
                return

            url = f"http://{short_domain}/"
            st.info(f"Pinging {url}...")

            if domain_precheck(short_domain):
                st.success("Domain is accessible. Proceeding with scan.")
            else:
                st.error("Domain is not accessible. Scan cannot proceed.")
                return

        with col2:
            case_comment = st.text_area("Case comment", height=100)

            page_search = st.checkbox("Use PageSearch function?", value=False)

            if page_search:
                keywords_input = st.text_input("Keywords (comma-separated)", placeholder="keyword1, keyword2")
                if keywords_input.strip():
                    keywords_list = [k.strip() for k in keywords_input.split(',') if k.strip()]
                    if not keywords_list:
                        st.error("This field must contain at least one keyword")
                        return
                    keywords = keywords_list
                    pagesearch_ui_mark = f'Yes, with {keywords_list} keywords search'
                else:
                    keywords = None
                    pagesearch_ui_mark = 'Yes, without keywords search'
            else:
                keywords = None
                pagesearch_ui_mark = 'No'

        dorking_raw = st.selectbox(
            "Dorking mode",
            ["Basic", "IoT", "Files", "Admins", "Web", "Custom", "N"]
        )

        if dorking_raw == "Custom":
            custom_db_name = st.text_input("Enter your custom Dorking DB name (no extension)")
            try:
                sanitize_db_filename(custom_db_name)
            except ValueError as e:
                st.error(str(e))
                return
            dorking_flag = f'custom+{custom_db_name}.db'
        elif dorking_raw == "N":
            dorking_flag = 'n'
        else:
            dorking_flag = dorking_raw.lower()

        api_yes = st.checkbox("Use 3rd party API in scan?", value=False)

        used_api_ids: List[str] = ['Empty']
        username: Optional[str] = None
        used_api_ui = 'No'

        if api_yes:
            db.select_api_keys('printing')
            st.info("⚠️ APIs with red-colored API Key field are unable to use!")

            to_use_api_flag = st.text_input(
                "Select APIs IDs (comma-separated)",
                placeholder="1,2,3"
            )
            used_api_ids = [item.strip() for item in to_use_api_flag.split(',') if item.strip().isdigit()]

            if not used_api_ids:
                st.error("No valid API IDs selected")
                return

            if '3' in used_api_ids:
                u = st.text_input("Username from this domain (or leave empty)", placeholder="username")
                username = None if not u else u

            if db.check_api_keys(used_api_ids):
                st.success('Found API key. Continuation')
            else:
                st.error("API key was not found. Check if you've entered valid API key in API Keys DB")
                return

            used_api_ui = f'Yes, using APIs with following IDs: {", ".join(used_api_ids)}'

        snap_choice = st.selectbox(
            "Snapshotting mode",
            ["S(creenshot)", "P(age Copy)", "W(ayback Machine)", "N"]
        )

        snapshotting_ui_mark = 'No'
        from_date = end_date = 'N'

        if snap_choice == "S(creenshot)":
            snapshotting_ui_mark = "Yes, domain's main page snapshotting as a screenshot"
        elif snap_choice == "P(age Copy)":
            snapshotting_ui_mark = "Yes, domain's main page snapshotting as a .HTML file"
        elif snap_choice == "W(ayback Machine)":
            from_date = st.text_input('Start date (YYYYMMDD format)', placeholder="20230101")
            end_date = st.text_input('End date (YYYYMMDD format)', placeholder="20241231")
            if not (validate_yyyymmdd(from_date) and validate_yyyymmdd(end_date)):
                st.error("Invalid date format. Use YYYYMMDD.")
                return
            snapshotting_ui_mark = "Yes, domain's main page snapshotting using Wayback Machine"

        dorking_ui_mark = compute_dorking_ui_mark(dorking_flag)

        cli_init.print_prescan_summary(
            short_domain, report_type.value.upper(), pagesearch_ui_mark,
            dorking_ui_mark, used_api_ui, case_comment, snapshotting_ui_mark
        )

        options = ScanOptions(
            short_domain=short_domain,
            url=url,
            case_comment=case_comment,
            report_type=report_type,
            page_search=page_search,
            keywords=keywords,
            dorking_flag=dorking_flag,
            used_api_ids=used_api_ids,
            snapshot_mode=snap_choice.lower(),
            username=username,
            wb_from=from_date,
            wb_to=end_date,
            pagesearch_ui_mark=pagesearch_ui_mark,
            snapshotting_ui_mark=snapshotting_ui_mark,
        )

        try:
            process_report(options)
        except Exception as e:
            st.error("Error appeared during report processing. See journal for details")
            logging.error("PROCESS REPORT ERROR: %s", e, exc_info=True)


def handle_settings():
    with st.container(border=True):
        config = print_and_return_config()

        col1, col2 = st.columns(2)

        with col1:
            section = st.selectbox("\nEnter the section you want to update", list(config.sections()))

            options = [opt for opt in config.options(section)]
            option = st.selectbox("Enter the option you want to update", options)

            value = st.text_input("Enter the new value")

        with col2:
            if st.button("Update Configuration"):
                config.set(section.upper(), option, value)
                with open(CONFIG_PATH, 'w') as configfile:
                    config.write(configfile)
                st.success("\nConfiguration updated successfully")


def handle_dorking_db():
    cli.dorking_db_manager()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Create Custom Dorking DB"):
            try:
                ddb_name = sanitize_db_filename(st.text_input("Enter a name for your custom Dorking DB (no extension)"))
            except ValueError as e:
                st.error(str(e))
                return
            manage_dorks(ddb_name)


def handle_db_menu():
    with st.container(border=True):
        rsdb_presence = db.check_rsdb_presence('report_storage.db')

        if rsdb_presence:
            st.success("Report storage database presence: OK")
        else:
            db.db_creation('report_storage.db')
            st.success("Successfully created report storage database")

        col1, col2 = st.columns(2)

        with col1:
            choice_db = st.selectbox("\nDatabase actions", ["Select reports", "Close connection"])

            if choice_db == "Select reports":
                cursor, sqlite_connection, data_presence_flag = db.db_select()

                if data_presence_flag:
                    id_to_extract_raw = st.text_input("Enter report ID to extract")

                    if id_to_extract_raw.isdigit():
                        id_to_extract = int(id_to_extract_raw)
                        extracted_folder_name = f'report_recreated_ID#{id_to_extract}'

                        try:
                            os.makedirs(extracted_folder_name)
                            db.db_report_recreate(extracted_folder_name, id_to_extract)
                            st.success(f"Report {id_to_extract} recreated in folder '{extracted_folder_name}'")
                        except FileExistsError:
                            st.error("Report with the same recreated folder already exists. Please check its content or delete it and try again")
                        except Exception as e:
                            st.error("Error appeared when trying to recreate report from DB. See journal for details")
                            logging.error("REPORT RECREATE ERROR: %s", e, exc_info=True)

        with col2:
            if st.button("Close connection"):
                db.db_select()
                st.success("\nDatabase connection is successfully closed")


def handle_docs():
    st.link_button("📚 Documentation", "https://dpulse.readthedocs.io/en/latest/")


def handle_api_manager():
    cli.api_manager()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Update API Key"):
            cursor, conn = db.select_api_keys('updating')

            api_id_to_update = st.text_input("\nEnter API's ID to update its key")
            new_api_key = st.text_input("Enter new API key")

            try:
                cursor.execute("UPDATE api_keys SET api_key = ? WHERE id = ?", (new_api_key, api_id_to_update))
                conn.commit()
                st.success("\nSuccessfully added new API key")
            except Exception as e:
                st.error("Something went wrong when adding new API key. See journal for details")
                logging.error('API KEY ADDING: ERROR. REASON: %s', e, exc_info=True)

            try:
                conn.close()
            except Exception:
                pass

    with col2:
        if st.button("Reset API Keys DB"):
            try:
                (APIS_DIR / 'api_keys.db').unlink(missing_ok=True)
                st.success("Deleted old API Keys DB")
            except Exception as e:
                st.error("Failed to delete old API Keys DB")
                logging.error("DELETE API DB ERROR: %s", e, exc_info=True)

            try:
                shutil.copyfile(APIS_DIR / 'api_keys_reference.db', APIS_DIR / 'api_keys.db')
                st.success("Successfully restored reference API Keys DB")
            except FileNotFoundError:
                st.error("Reference API Keys DB was not found")
            except Exception as e:
                st.error("Failed to restore API Keys DB")
                logging.error("RESTORE API DB ERROR: %s", e, exc_info=True)


def handle_exit():
    st.warning("Exiting the program.")
    raise SystemExit


HANDLERS: Dict[str, Callable[[], None]] = {
    "1": handle_scan,
    "2": handle_settings,
    "3": handle_dorking_db,
    "4": handle_db_menu,
    "5": handle_api_manager,
    "6": handle_docs,
    "7": handle_exit,
}


def bootstrap():
    cfg_presence = check_cfg_presence()

    if cfg_presence:
        st.success("Global config file presence: OK")
    else:
        st.warning("Global config file presence: NOT OK")
        create_config()
        st.success("Successfully generated global config file")

    rsdb_presence = db.check_rsdb_presence('report_storage.db')

    if rsdb_presence:
        st.success("Report storage database presence: OK")
    else:
        db.db_creation('report_storage.db')
        st.success("Successfully created report storage database")

    dorks_files_check()

    try:
        _ = read_config()
        print('')
    except Exception as e:
        logging.error("CONFIG READ ERROR: %s", e, exc_info=True)
        st.error("Failed to read config. See journal for details")


def run():
    with st.container():
        #cli.welcome_menu()

        col1, col2 = st.columns(7)

        HANDLERS["1"] = handle_scan
        HANDLERS["2"] = handle_settings
        HANDLERS["3"] = handle_dorking_db
        HANDLERS["4"] = handle_db_menu
        HANDLERS["5"] = handle_api_manager
        HANDLERS["6"] = handle_docs
        HANDLERS["7"] = handle_exit

        for i, handler in HANDLERS.items():
            with col1:
                st.button(f"{i}", on_click=handler)


def main():
    bootstrap()
    run()


if __name__ == "__main__":
    main()
