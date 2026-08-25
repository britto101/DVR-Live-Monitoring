import base64
import datetime
import hashlib
import io
import os
import random
import socket
import threading
import time

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "DVR Live Monitoring"

SOCKET_TIMEOUT = 5.0
REQUEST_RETRIES = 3
MAX_WORKERS = 10

AUTO_REFRESH_SECONDS = 60

# ============================================================
# EXCEL FILE
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

EXCEL_FILE = os.path.join(
    BASE_DIR,
    "DVRlist (1).xlsx"
)


# ============================================================
# EASY4IP CREDENTIALS
# ============================================================
# Read securely from Streamlit Secrets.
#
# Local:
#   .streamlit/secrets.toml
#
# Streamlit Cloud:
#   App -> Settings -> Secrets
#
# Never commit secrets.toml to GitHub.

try:
    USERNAME = st.secrets["EASY4IP_USERNAME"]
    USERKEY = st.secrets["EASY4IP_USERKEY"]
    RANDSALT = st.secrets["EASY4IP_RANDSALT"]
except Exception as e:
    raise RuntimeError(
        "Missing Easy4IP secrets. Add EASY4IP_USERNAME, "
        "EASY4IP_USERKEY and EASY4IP_RANDSALT to "
        ".streamlit/secrets.toml or Streamlit Cloud Secrets."
    ) from e


# ============================================================
# MAIN P2P SERVERS
# ============================================================

MAIN_SERVERS = [
    ("www.easy4ipcloud.com", 8800),
    ("www.dahuap2pcloud.com", 8800),
]


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📹",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SESSION STATE
# ============================================================

def initialize_state():

    if "dvr_data" not in st.session_state:
        st.session_state.dvr_data = pd.DataFrame(
            columns=[
                "Store ID",
                "Site Name",
                "DVR Number",
                "Status"
            ]
        )

    if "scan_running" not in st.session_state:
        st.session_state.scan_running = False

    if "scan_completed" not in st.session_state:
        st.session_state.scan_completed = 0

    if "scan_total" not in st.session_state:
        st.session_state.scan_total = 0

    if "scan_started_at" not in st.session_state:
        st.session_state.scan_started_at = None

    if "last_scan_time" not in st.session_state:
        st.session_state.last_scan_time = None

    if "last_auto_refresh_count" not in st.session_state:
        st.session_state.last_auto_refresh_count = 0

    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    if "loaded" not in st.session_state:
        st.session_state.loaded = False

    if "load_error" not in st.session_state:
        st.session_state.load_error = ""

    if "last_message" not in st.session_state:
        st.session_state.last_message = ""


initialize_state()


# ============================================================
# SERIAL NORMALIZATION
# ============================================================

def normalize_serial(value):

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except Exception:
        pass

    text = str(value).strip()

    if text.lower() in (
        "nan",
        "none",
        "null"
    ):
        return ""

    if text.endswith(".0"):

        possible = text[:-2]

        if possible.isdigit():
            text = possible

    return text


# ============================================================
# FIND COLUMN
# ============================================================

def clean_column_name(name):

    return (
        str(name)
        .strip()
        .lower()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
    )


def find_column(
    columns_list,
    possible_names
):

    normalized = {}

    for col in columns_list:

        clean = clean_column_name(
            col
        )

        normalized[clean] = col

    for name in possible_names:

        clean_name = clean_column_name(
            name
        )

        if clean_name in normalized:

            return normalized[
                clean_name
            ]

    return None


# ============================================================
# LOAD EXCEL
# ============================================================

def load_excel():

    if not os.path.isfile(EXCEL_FILE):

        st.session_state.load_error = (
            "Excel file not found:\n\n"
            + EXCEL_FILE
        )

        st.session_state.dvr_data = pd.DataFrame(
            columns=[
                "Store ID",
                "Site Name",
                "DVR Number",
                "Status"
            ]
        )

        return False

    try:

        data = pd.read_excel(
            EXCEL_FILE,
            dtype=str,
            engine="openpyxl"
        )

        # ----------------------------------------------------
        # Remove completely empty rows/columns
        # ----------------------------------------------------

        data = data.dropna(
            axis=1,
            how="all"
        )

        data = data.dropna(
            axis=0,
            how="all"
        )

        # ----------------------------------------------------
        # Clean column names
        # ----------------------------------------------------

        data.columns = [
            str(col).strip()
            for col in data.columns
        ]

        print(
            "Excel columns:",
            list(data.columns)
        )

        # ----------------------------------------------------
        # Find Store ID
        # ----------------------------------------------------

        store_column = find_column(
            data.columns,
            [
                "Store ID",
                "StoreID",
                "Store",
                "Store No",
                "Store Number",
                "Branch ID",
                "Branch",
                "Branch Number"
            ]
        )

        # ----------------------------------------------------
        # Find Site Name
        # ----------------------------------------------------

        site_column = find_column(
            data.columns,
            [
                "Site Name",
                "SiteName",
                "Site",
                "Location",
                "Store Name",
                "Branch Name"
            ]
        )

        # ----------------------------------------------------
        # Find DVR Number
        # ----------------------------------------------------

        dvr_column = find_column(
            data.columns,
            [
                "DVR Number",
                "DVRNumber",
                "DVR",
                "DVR No",
                "DVRNo",
                "P2P",
                "P2P Number",
                "P2PNo",
                "P2P No",
                "Serial",
                "Serial Number",
                "Device Serial",
                "Device Serial Number"
            ]
        )

        # ----------------------------------------------------
        # DVR column is mandatory
        # ----------------------------------------------------

        if dvr_column is None:

            st.session_state.load_error = (
                "DVR/P2P column was not found in the Excel file.\n\n"
                "Columns found:\n"
                + ", ".join(
                    str(x)
                    for x in data.columns
                )
            )

            st.session_state.dvr_data = pd.DataFrame(
                columns=[
                    "Store ID",
                    "Site Name",
                    "DVR Number",
                    "Status"
                ]
            )

            return False

        # ----------------------------------------------------
        # Create clean dataframe
        # ----------------------------------------------------

        clean_data = pd.DataFrame()

        if store_column is not None:

            clean_data["Store ID"] = (
                data[
                    store_column
                ]
                .fillna("")
                .apply(
                    normalize_serial
                )
            )

        else:

            clean_data["Store ID"] = ""

        if site_column is not None:

            clean_data["Site Name"] = (
                data[
                    site_column
                ]
                .fillna("")
                .apply(
                    normalize_serial
                )
            )

        else:

            clean_data["Site Name"] = ""

        clean_data["DVR Number"] = (
            data[
                dvr_column
            ]
            .fillna("")
            .apply(
                normalize_serial
            )
        )

        # ----------------------------------------------------
        # Status ONLY exists in memory
        # ----------------------------------------------------

        clean_data["Status"] = "Not Checked"

        # ----------------------------------------------------
        # Remove rows without DVR number
        # ----------------------------------------------------

        clean_data = clean_data[
            clean_data[
                "DVR Number"
            ]
            .astype(str)
            .str.strip()
            != ""
        ].copy()

        clean_data.reset_index(
            drop=True,
            inplace=True
        )

        # ----------------------------------------------------
        # Guarantee exact columns
        # ----------------------------------------------------

        clean_data = clean_data[
            [
                "Store ID",
                "Site Name",
                "DVR Number",
                "Status"
            ]
        ]

        st.session_state.dvr_data = (
            clean_data
        )

        st.session_state.loaded = True
        st.session_state.load_error = ""

        return True

    except Exception as e:

        st.session_state.load_error = (
            "Excel loading error:\n\n"
            + str(e)
        )

        st.session_state.dvr_data = pd.DataFrame(
            columns=[
                "Store ID",
                "Site Name",
                "DVR Number",
                "Status"
            ]
        )

        return False


# ============================================================
# SAVE EXCEL
# ============================================================

def save_excel_file():

    try:

        data = st.session_state.dvr_data

        # ----------------------------------------------------
        # Safety check
        # ----------------------------------------------------

        if data is None:

            return False, "No DVR data."

        if data.empty:

            return False, "No DVR data to save."

        # ----------------------------------------------------
        # Guarantee columns exist
        # ----------------------------------------------------

        for column in [
            "Store ID",
            "Site Name",
            "DVR Number"
        ]:

            if column not in data.columns:

                data[column] = ""

        # ----------------------------------------------------
        # Save ONLY permanent columns
        # ----------------------------------------------------

        excel_data = pd.DataFrame({

            "Store ID": [
                normalize_serial(x)
                for x in data[
                    "Store ID"
                ]
            ],

            "Site Name": [
                normalize_serial(x)
                for x in data[
                    "Site Name"
                ]
            ],

            "DVR Number": [
                normalize_serial(x)
                for x in data[
                    "DVR Number"
                ]
            ]

        })

        excel_data.to_excel(
            EXCEL_FILE,
            index=False,
            engine="openpyxl"
        )

        return (
            True,
            "Excel file saved successfully."
        )

    except PermissionError:

        return (
            False,
            "Permission denied. "
            "Please close the Excel file before saving."
        )

    except Exception as e:

        return (
            False,
            f"Excel save error: {e}"
        )


# ============================================================
# UDP CLIENT
# ============================================================

class UDPClient:

    def __init__(
        self,
        host,
        port,
        timeout=SOCKET_TIMEOUT
    ):

        self.host = host
        self.port = port

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.sock.settimeout(
            timeout
        )

    def close(self):

        try:
            self.sock.close()

        except Exception:
            pass

    def request(
        self,
        path,
        retries=REQUEST_RETRIES
    ):

        last_error = None

        for attempt in range(
            retries
        ):

            try:

                nonce = random.randrange(
                    2 ** 31
                )

                curdate = (
                    datetime.datetime.utcnow()
                    .strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                )

                pwd = (
                    f"{nonce}"
                    f"{curdate}"
                    f"DHP2P:"
                    f"{USERNAME}:"
                    f"{USERKEY}"
                )

                digest = (
                    base64.b64encode(
                        hashlib.sha1(
                            pwd.encode()
                        ).digest()
                    )
                    .decode()
                )

                request = (
                    f"DHGET {path} HTTP/1.1\r\n"
                    f"CSeq: {nonce}\r\n"
                    f'Authorization: WSSE profile="UsernameToken"\r\n'
                    f'X-WSSE: UsernameToken '
                    f'Username="{USERNAME}", '
                    f'PasswordDigest="{digest}", '
                    f'Nonce="{nonce}", '
                    f'Created="{curdate}"\r\n'
                    f"\r\n"
                )

                self.sock.sendto(
                    request.encode(),
                    (
                        self.host,
                        self.port
                    )
                )

                response_data, address = (
                    self.sock.recvfrom(
                        16384
                    )
                )

                response = parse_response(
                    response_data.decode(
                        errors="ignore"
                    )
                )

                response["address"] = address

                return response

            except socket.timeout as e:

                last_error = e

                if attempt < retries - 1:
                    time.sleep(0.2)

            except Exception as e:

                last_error = e

                if attempt < retries - 1:
                    time.sleep(0.2)

        if last_error:

            raise last_error

        raise RuntimeError(
            "UDP request failed"
        )


# ============================================================
# RESPONSE PARSER
# ============================================================

def parse_response(data):

    result = {
        "code": 500,
        "body": "",
        "headers": {}
    }

    try:

        parts = data.split(
            "\r\n\r\n",
            1
        )

        headers_part = parts[0]

        if len(parts) > 1:

            result["body"] = parts[1]

        lines = headers_part.split(
            "\r\n"
        )

        if not lines:

            return result

        first = lines[0].split(
            " ",
            2
        )

        if len(first) >= 2:

            try:

                result["code"] = int(
                    first[1]
                )

            except Exception:
                pass

        for line in lines[1:]:

            if ":" in line:

                key, value = line.split(
                    ":",
                    1
                )

                result[
                    "headers"
                ][
                    key.strip().lower()
                ] = value.strip()

        return result

    except Exception:

        return result


# ============================================================
# P2P ENDPOINT
# ============================================================

def parse_endpoint(value):

    if not value:
        return None

    value = value.strip()

    if ":" not in value:
        return None

    host, port_text = value.rsplit(
        ":",
        1
    )

    host = host.strip(
        "\"'<> "
    )

    port_text = port_text.strip(
        "\"'<> "
    )

    if not host:
        return None

    try:

        port = int(
            port_text
        )

    except ValueError:

        return None

    if port < 1 or port > 65535:

        return None

    return host, port


def extract_p2p_endpoint(body):

    if not body:
        return None

    text = body.strip()

    # --------------------------------------------------------
    # Normal <US>...</US>
    # --------------------------------------------------------

    start = text.find(
        "<US>"
    )

    if start != -1:

        start += 4

        end = text.find(
            "</US>",
            start
        )

        if end != -1:

            endpoint = parse_endpoint(
                text[start:end].strip()
            )

            if endpoint:

                return endpoint

    # --------------------------------------------------------
    # Case insensitive
    # --------------------------------------------------------

    upper = text.upper()

    start = upper.find(
        "<US>"
    )

    if start != -1:

        start += 4

        end = upper.find(
            "</US>",
            start
        )

        if end != -1:

            endpoint = parse_endpoint(
                text[start:end].strip()
            )

            if endpoint:

                return endpoint

    # --------------------------------------------------------
    # Search individual tokens
    # --------------------------------------------------------

    for token in (
        text
        .replace(
            "\r",
            " "
        )
        .replace(
            "\n",
            " "
        )
        .split()
    ):

        token = (
            token
            .replace(
                "<US>",
                ""
            )
            .replace(
                "</US>",
                ""
            )
            .strip(
                "\"'<>;,"
            )
        )

        endpoint = parse_endpoint(
            token
        )

        if endpoint:

            return endpoint

    return None


# ============================================================
# RESOLVE P2P SERVER
# ============================================================

def resolve_p2psrv(serial):

    serial = normalize_serial(
        serial
    )

    if not serial:

        return None

    for server, port in MAIN_SERVERS:

        client = None

        try:

            client = UDPClient(
                server,
                port,
                SOCKET_TIMEOUT
            )

            response = client.request(
                f"/online/p2psrv/{serial}"
            )

            code = response.get(
                "code",
                500
            )

            body = response.get(
                "body",
                ""
            )

            print(
                f"[P2P RESOLVE] "
                f"{serial} -> "
                f"{server}:{port} "
                f"HTTP {code}"
            )

            if code >= 400:

                continue

            endpoint = extract_p2p_endpoint(
                body
            )

            if endpoint:

                print(
                    f"[P2P SERVER] "
                    f"{serial} -> "
                    f"{endpoint[0]}:{endpoint[1]}"
                )

                return endpoint

        except Exception as e:

            print(
                f"[P2P RESOLVE ERROR] "
                f"{serial}: {e}"
            )

        finally:

            if client:

                client.close()

    return None


# ============================================================
# CHECK DVR
# ============================================================

def check_dvr_status(
    dvr_number
):

    serial = normalize_serial(
        dvr_number
    )

    if not serial:

        return "Offline"

    endpoint = resolve_p2psrv(
        serial
    )

    if not endpoint:

        print(
            f"[OFFLINE] "
            f"{serial} - "
            f"could not resolve P2P server"
        )

        return "Offline"

    host, port = endpoint

    client = None

    try:

        client = UDPClient(
            host,
            port,
            SOCKET_TIMEOUT
        )

        # ----------------------------------------------------
        # PROBE
        # ----------------------------------------------------

        probe = client.request(
            f"/probe/device/{serial}",
            retries=REQUEST_RETRIES
        )

        probe_code = probe.get(
            "code",
            500
        )

        print(
            f"[PROBE] "
            f"{serial} -> "
            f"{host}:{port} "
            f"HTTP {probe_code}"
        )

        if 200 <= probe_code < 300:

            print(
                f"[ONLINE] {serial}"
            )

            return "Online"

        # ----------------------------------------------------
        # INFO FALLBACK
        # ----------------------------------------------------

        info = client.request(
            f"/info/device/{serial}",
            retries=REQUEST_RETRIES
        )

        info_code = info.get(
            "code",
            500
        )

        print(
            f"[INFO] "
            f"{serial} -> "
            f"HTTP {info_code}"
        )

        if 200 <= info_code < 300:

            print(
                f"[ONLINE] {serial}"
            )

            return "Online"

        print(
            f"[OFFLINE] "
            f"{serial} "
            f"(probe={probe_code}, "
            f"info={info_code})"
        )

        return "Offline"

    except socket.timeout:

        print(
            f"[TIMEOUT] {serial}"
        )

        return "Offline"

    except Exception as e:

        print(
            f"[CHECK ERROR] "
            f"{serial}: {e}"
        )

        return "Offline"

    finally:

        if client:

            client.close()


# ============================================================
# CHECK ALL
# ============================================================

def run_check_all():

    data = st.session_state.dvr_data

    if data.empty:

        return

    indexes = list(
        data.index
    )

    st.session_state.scan_running = True
    st.session_state.scan_completed = 0
    st.session_state.scan_total = len(
        indexes
    )
    st.session_state.scan_started_at = time.time()

    # --------------------------------------------------------
    # Set everything to Checking
    # --------------------------------------------------------

    for index in indexes:

        st.session_state.dvr_data.loc[
            index,
            "Status"
        ] = "Checking..."

    # --------------------------------------------------------
    # Progress UI
    # --------------------------------------------------------

    progress = st.progress(
        0
    )

    progress_text = st.empty()

    # --------------------------------------------------------
    # Thread pool
    # --------------------------------------------------------

    workers = min(
        MAX_WORKERS,
        max(
            1,
            len(indexes)
        )
    )

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = {}

        for index in indexes:

            serial = normalize_serial(
                st.session_state.dvr_data.loc[
                    index,
                    "DVR Number"
                ]
            )

            future = executor.submit(
                check_dvr_status,
                serial
            )

            futures[future] = index

        for future in as_completed(
            futures
        ):

            index = futures[
                future
            ]

            try:

                status = future.result()

            except Exception as e:

                print(
                    f"[SCAN ERROR] "
                    f"{index}: {e}"
                )

                status = "Offline"

            st.session_state.dvr_data.loc[
                index,
                "Status"
            ] = status

            st.session_state.scan_completed += 1

            completed = (
                st.session_state.scan_completed
            )

            total = (
                st.session_state.scan_total
            )

            percent = (
                completed / total
                if total
                else 0
            )

            progress.progress(
                percent
            )

            progress_text.write(
                f"Checking "
                f"{completed} / {total} "
                f"DVRs "
                f"({int(percent * 100)}%)"
            )

    st.session_state.scan_running = False

    st.session_state.last_scan_time = (
        datetime.datetime.now()
    )

    progress.progress(
        1.0
    )

    progress_text.success(
        "DVR scan completed."
    )


# ============================================================
# CHECK ONE DVR
# ============================================================

def check_one_dvr(
    serial
):

    serial = normalize_serial(
        serial
    )

    if not serial:

        return "Offline"

    status = check_dvr_status(
        serial
    )

    data = st.session_state.dvr_data

    if not data.empty:

        matches = (
            data[
                "DVR Number"
            ]
            .astype(str)
            .apply(
                normalize_serial
            )
            == serial
        )

        for index in data[
            matches
        ].index:

            st.session_state.dvr_data.loc[
                index,
                "Status"
            ] = status

    return status


# ============================================================
# DASHBOARD COUNTS
# ============================================================

def get_counts():

    data = st.session_state.dvr_data

    if data is None or data.empty:

        return {
            "total": 0,
            "online": 0,
            "offline": 0,
            "checking": 0,
            "not_checked": 0
        }

    # --------------------------------------------------------
    # Guarantee Status column
    # --------------------------------------------------------

    if "Status" not in data.columns:

        data["Status"] = "Not Checked"

    return {

        "total": len(data),

        "online": int(
            (
                data["Status"]
                == "Online"
            ).sum()
        ),

        "offline": int(
            (
                data["Status"]
                == "Offline"
            ).sum()
        ),

        "checking": int(
            (
                data["Status"]
                == "Checking..."
            ).sum()
        ),

        "not_checked": int(
            (
                data["Status"]
                == "Not Checked"
            ).sum()
        )

    }


# ============================================================
# CSV
# ============================================================

def create_csv():

    data = st.session_state.dvr_data.copy()

    # --------------------------------------------------------
    # SAFETY: never assume Store ID exists
    # --------------------------------------------------------

    required_columns = [
        "Store ID",
        "Site Name",
        "DVR Number",
        "Status"
    ]

    for column in required_columns:

        if column not in data.columns:

            data[column] = ""

    data = data[
        required_columns
    ]

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    for column in required_columns:

        data[column] = data[
            column
        ].apply(
            normalize_serial
        )

    return data.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )


# ============================================================
# CSS
# ============================================================

def apply_css():

    dark = st.session_state.dark_mode

    if dark:

        background = "#111718"
        card_background = "#1d2425"
        text = "#ffffff"
        border = "#333b3c"
        input_background = "#1d2425"

    else:

        background = "#f2f7f7"
        card_background = "#ffffff"
        text = "#263238"
        border = "#d7e4e4"
        input_background = "#ffffff"

    st.markdown(
        f"""
        <style>

        .stApp {{
            background: {background};
            color: {text};
        }}

        .main-header {{
            background: #007e82;
            color: white;
            padding: 22px 30px;
            border-radius: 10px;
            margin-bottom: 18px;
        }}

        .main-title-text {{
            font-size: 28px;
            font-weight: 700;
        }}

        .main-subtitle {{
            font-size: 13px;
            color: #b8eeee;
            margin-top: 4px;
        }}

        .metric-card {{
            border-radius: 10px;
            padding: 18px;
            min-height: 110px;
            color: white;
            box-shadow:
                0 3px 8px rgba(
                    0,
                    0,
                    0,
                    0.16
                );
        }}

        .metric-title {{
            font-size: 13px;
            font-weight: 700;
        }}

        .metric-value {{
            font-size: 34px;
            font-weight: 700;
            margin-top: 10px;
        }}

        .metric-total {{
            background: #00a7a5;
        }}

        .metric-online {{
            background: #159447;
        }}

        .metric-offline {{
            background: #d9363e;
        }}

        .metric-checking {{
            background: #1769aa;
        }}

        .metric-notchecked {{
            background: #607d8b;
        }}

        .section-box {{
            background: {card_background};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 14px;
        }}

        .section-title {{
            color: #007e82;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 8px;
        }}

        .status-online {{
            color: #159447;
            font-weight: 700;
        }}

        .status-offline {{
            color: #d9363e;
            font-weight: 700;
        }}

        .status-checking {{
            color: #1769aa;
            font-weight: 700;
        }}

        .status-notchecked {{
            color: #607d8b;
            font-weight: 700;
        }}

        div[data-testid="stMetric"] {{
            background: {card_background};
            border: 1px solid {border};
            padding: 12px;
            border-radius: 8px;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# HEADER
# ============================================================

def render_header():

    st.html(
        """
        <div class="main-header">
            <div class="main-title-text">📹 DVR LIVE MONITORING</div>
            <div class="main-subtitle">Automatic P2P DVR monitoring</div>
        </div>
        """
    )


# ============================================================
# METRICS
# ============================================================

def render_metrics():

    counts = get_counts()

    cards = [
        ("📹 TOTAL DVR", counts["total"], "metric-total"),
        ("✓ ONLINE", counts["online"], "metric-online"),
        ("! OFFLINE", counts["offline"], "metric-offline"),
        ("↻ CHECKING", counts["checking"], "metric-checking"),
        ("○ NOT CHECKED", counts["not_checked"], "metric-notchecked"),
    ]

    columns = st.columns(5)

    for column, (title, value, css_class) in zip(columns, cards):
        with column:
            st.html(
                f"""
                <div class="metric-card {css_class}">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """
            )


# ============================================================
# TOOLBAR
# ============================================================

def render_toolbar():

    st.markdown(
        '<div class="section-box">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">CONTROL PANEL</div>',
        unsafe_allow_html=True
    )

    columns = st.columns(
        7
    )

    # --------------------------------------------------------
    # Check All
    # --------------------------------------------------------

    with columns[0]:

        if st.button(
            "🌐 Check All",
            use_container_width=True,
            type="primary",
            disabled=(
                st.session_state.scan_running
                or
                st.session_state.dvr_data.empty
            )
        ):

            run_check_all()

            st.rerun()

    # --------------------------------------------------------
    # Refresh
    # --------------------------------------------------------

    with columns[1]:

        if st.button(
            "🔄 Refresh All",
            use_container_width=True,
            disabled=(
                st.session_state.scan_running
                or
                st.session_state.dvr_data.empty
            )
        ):

            # Refresh All means CHECK ALL DVRs immediately.
            # It must not reload the Excel and reset statuses.
            run_check_all()

            st.rerun()

    # --------------------------------------------------------
    # Show All
    # --------------------------------------------------------

    with columns[2]:

        if st.button(
            "📋 Show All",
            use_container_width=True
        ):

            st.session_state.search_text = ""

            st.rerun()

    # --------------------------------------------------------
    # Export CSV
    # --------------------------------------------------------

    with columns[3]:

        csv_data = create_csv()

        st.download_button(
            "📥 Export CSV",
            data=csv_data,
            file_name="DVR_Status_Result.csv",
            mime="text/csv",
            use_container_width=True
        )

    # --------------------------------------------------------
    # Save Excel
    # --------------------------------------------------------

    with columns[4]:

        if st.button(
            "💾 Save Excel",
            use_container_width=True
        ):

            success, message = (
                save_excel_file()
            )

            if success:

                st.success(
                    message
                )

            else:

                st.error(
                    message
                )

    # --------------------------------------------------------
    # Dark Mode
    # --------------------------------------------------------

    with columns[5]:

        if st.button(
            (
                "☀️ Light Mode"
                if st.session_state.dark_mode
                else
                "🌙 Dark Mode"
            ),
            use_container_width=True
        ):

            st.session_state.dark_mode = (
                not st.session_state.dark_mode
            )

            st.rerun()

    # --------------------------------------------------------
    # Reload Excel
    # --------------------------------------------------------

    with columns[6]:

        if st.button(
            "📂 Reload Excel",
            use_container_width=True
        ):

            load_excel()

            st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# SEARCH
# ============================================================

def render_search():

    st.markdown(
        '<div class="section-box">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">🔍 DEVICE SEARCH</div>',
        unsafe_allow_html=True
    )

    columns = st.columns(
        [
            3,
            1,
            1,
            1
        ]
    )

    with columns[0]:

        search = st.text_input(
            "Search",
            placeholder=(
                "Store ID, Site Name or DVR Number"
            ),
            key="search_text"
        )

    with columns[1]:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Online",
                "Offline",
                "Checking...",
                "Not Checked"
            ]
        )

    with columns[2]:

        check_serial = st.text_input(
            "Check One DVR",
            placeholder="DVR/P2P Number"
        )

    with columns[3]:

        if st.button(
            "🔍 Check One",
            use_container_width=True
        ):

            if not check_serial.strip():

                st.warning(
                    "Enter a DVR/P2P serial number."
                )

            else:

                with st.spinner(
                    f"Checking {check_serial}..."
                ):

                    status = check_one_dvr(
                        check_serial
                    )

                if status == "Online":

                    st.success(
                        f"{check_serial}: Online"
                    )

                else:

                    st.error(
                        f"{check_serial}: Offline"
                    )

                st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    return (
        search,
        status_filter
    )


# ============================================================
# FILTER DATA
# ============================================================

def filter_data(
    search,
    status_filter
):

    data = (
        st.session_state.dvr_data
        .copy()
    )

    if data.empty:

        return data

    # --------------------------------------------------------
    # Guarantee columns
    # --------------------------------------------------------

    for column in [
        "Store ID",
        "Site Name",
        "DVR Number",
        "Status"
    ]:

        if column not in data.columns:

            data[column] = ""

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    search = (
        search
        or ""
    ).strip().lower()

    if search:

        searchable = (
            data["Store ID"]
            .astype(str)
            .str.lower()
            + " "
            +
            data["Site Name"]
            .astype(str)
            .str.lower()
            + " "
            +
            data["DVR Number"]
            .astype(str)
            .str.lower()
        )

        data = data[
            searchable.str.contains(
                search,
                na=False
            )
        ]

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if status_filter != "All":

        data = data[
            data["Status"]
            == status_filter
        ]

    return data


# ============================================================
# STATUS DISPLAY
# ============================================================

def style_status(
    value
):

    if value == "Online":

        return (
            "color: #159447; "
            "font-weight: bold;"
        )

    if value == "Offline":

        return (
            "color: #d9363e; "
            "font-weight: bold;"
        )

    if value == "Checking...":

        return (
            "color: #1769aa; "
            "font-weight: bold;"
        )

    return (
        "color: #607d8b; "
        "font-weight: bold;"
    )


# ============================================================
# TABLE
# ============================================================

def render_table(
    filtered_data
):

    st.markdown(
        '<div class="section-box">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">DVR LIST</div>',
        unsafe_allow_html=True
    )

    if filtered_data.empty:

        if st.session_state.dvr_data.empty:

            st.info(
                "No DVR records loaded."
            )

        else:

            st.info(
                "No DVR records found."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        return

    display_data = filtered_data[
        [
            "Store ID",
            "Site Name",
            "DVR Number",
            "Status"
        ]
    ].copy()

    styled = (
        display_data
        .style
        .map(
            style_status,
            subset=[
                "Status"
            ]
        )
    )

    st.dataframe(
        styled,
        width="stretch",
        height=500,
        hide_index=True
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# UPDATE DVR
# ============================================================

def render_update():

    st.markdown(
        '<div class="section-box">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">✏️ Select DVR for Update</div>',
        unsafe_allow_html=True
    )

    data = st.session_state.dvr_data

    if data.empty:

        st.info(
            "No DVR records available."
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        return

    options = []

    for index, row in data.iterrows():

        options.append(
            (
                index,
                (
                    f"{normalize_serial(row['Store ID'])}"
                    " | "
                    f"{normalize_serial(row['Site Name'])}"
                    " | "
                    f"{normalize_serial(row['DVR Number'])}"
                )
            )
        )

    labels = [
        x[1]
        for x in options
    ]

    selected_label = st.selectbox(
        "Select DVR",
        labels,
        key="selected_dvr"
    )

    selected_index = None

    for index, label in options:

        if label == selected_label:

            selected_index = index

            break

    if selected_index is None:

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        return

    row = data.loc[
        selected_index
    ]

    col1, col2, col3 = st.columns(
        3
    )

    with col1:

        store_id = st.text_input(
            "Store ID",
            value=normalize_serial(
                row["Store ID"]
            ),
            key="update_store"
        )

    with col2:

        site_name = st.text_input(
            "Site Name",
            value=normalize_serial(
                row["Site Name"]
            ),
            key="update_site"
        )

    with col3:

        dvr_number = st.text_input(
            "DVR Number",
            value=normalize_serial(
                row["DVR Number"]
            ),
            key="update_dvr"
        )

    col_save, col_check = st.columns(
        2
    )

    with col_save:

        if st.button(
            "💾 Update & Save",
            use_container_width=True,
            type="primary"
        ):

            dvr_number = normalize_serial(
                dvr_number
            )

            if not dvr_number:

                st.error(
                    "DVR Number is required."
                )

            else:

                st.session_state.dvr_data.loc[
                    selected_index,
                    "Store ID"
                ] = normalize_serial(
                    store_id
                )

                st.session_state.dvr_data.loc[
                    selected_index,
                    "Site Name"
                ] = normalize_serial(
                    site_name
                )

                st.session_state.dvr_data.loc[
                    selected_index,
                    "DVR Number"
                ] = dvr_number

                # Status is memory only
                st.session_state.dvr_data.loc[
                    selected_index,
                    "Status"
                ] = "Not Checked"

                success, message = (
                    save_excel_file()
                )

                if success:

                    st.success(
                        "DVR updated and saved permanently."
                    )

                else:

                    st.error(
                        message
                    )

    with col_check:

        if st.button(
            "🔍 Check Selected DVR",
            use_container_width=True
        ):

            serial = normalize_serial(
                dvr_number
            )

            if not serial:

                st.error(
                    "DVR Number is required."
                )

            else:

                with st.spinner(
                    f"Checking {serial}..."
                ):

                    status = check_one_dvr(
                        serial
                    )

                if status == "Online":

                    st.success(
                        f"{serial}: Online"
                    )

                else:

                    st.error(
                        f"{serial}: Offline"
                    )

                st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# FILE INFORMATION
# ============================================================

def render_file_info():

    st.markdown(
        '<div class="section-box">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">📁 EXCEL FILE</div>',
        unsafe_allow_html=True
    )

    st.write(
        EXCEL_FILE
    )

    if os.path.isfile(
        EXCEL_FILE
    ):

        file_size = os.path.getsize(
            EXCEL_FILE
        )

        modified = datetime.datetime.fromtimestamp(
            os.path.getmtime(
                EXCEL_FILE
            )
        )

        st.caption(
            f"Size: {file_size:,} bytes  |  "
            f"Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    else:

        st.error(
            "Excel file does not exist."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# AUTO REFRESH
# ============================================================

def auto_refresh():

    # Browser-side Streamlit rerun every 60 seconds.
    # st_autorefresh returns an increasing counter:
    #   0 = first page load
    #   1 = first automatic refresh
    #   2 = second automatic refresh
    #   ...
    #
    # We use the counter to run exactly one DVR scan per
    # automatic refresh. Manual st.rerun() does not increment it.

    refresh_count = st_autorefresh(
        interval=AUTO_REFRESH_SECONDS * 1000,
        key="dvr_auto_refresh"
    )

    return refresh_count


# ============================================================
# MAIN
# ============================================================

def main():

    apply_css()

    # --------------------------------------------------------
    # Initial Excel load
    # --------------------------------------------------------

    if not st.session_state.loaded:

        load_excel()

    # --------------------------------------------------------
    # Automatic 60-second refresh
    # --------------------------------------------------------
    refresh_count = auto_refresh()

    # Run exactly one complete DVR scan on each automatic
    # 60-second refresh. Do not run on the first page load.
    if (
        refresh_count > 0
        and not st.session_state.scan_running
        and not st.session_state.dvr_data.empty
        and st.session_state.get("last_auto_refresh_count") != refresh_count
    ):
        st.session_state.last_auto_refresh_count = refresh_count
        run_check_all()

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    render_header()

    # --------------------------------------------------------
    # Load error
    # --------------------------------------------------------

    if st.session_state.load_error:

        st.error(
            st.session_state.load_error
        )

        st.info(
            "Make sure your folder contains:\n\n"
            "DVRMonitoring/\n"
            "├── app.py\n"
            "├── requirements.txt\n"
            "└── DVRlist (1).xlsx"
        )

        # Still show controls so the user can reload.
    
    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    render_metrics()

    st.write("")

    # --------------------------------------------------------
    # Toolbar
    # --------------------------------------------------------

    render_toolbar()

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    search, status_filter = (
        render_search()
    )

    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    counts = get_counts()

    if st.session_state.scan_running:

        total = (
            st.session_state.scan_total
        )

        completed = (
            st.session_state.scan_completed
        )

        percent = (
            completed / total
            if total
            else 0
        )

        st.progress(
            percent
        )

        st.caption(
            f"Checking "
            f"{completed} / {total} DVRs "
            f"({int(percent * 100)}%)"
        )

    elif (
        st.session_state.last_scan_time
        is not None
    ):

        st.caption(
            "Last scan: "
            +
            st.session_state.last_scan_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    else:

        st.caption(
            f"Ready • Automatic scan every {AUTO_REFRESH_SECONDS} seconds"
        )

    # --------------------------------------------------------
    # Filter
    # --------------------------------------------------------

    filtered_data = filter_data(
        search,
        status_filter
    )

    # --------------------------------------------------------
    # Table
    # --------------------------------------------------------

    render_table(
        filtered_data
    )

    # --------------------------------------------------------
    # Update section
    # --------------------------------------------------------

    render_update()

    # --------------------------------------------------------
    # File information
    # --------------------------------------------------------

    render_file_info()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
