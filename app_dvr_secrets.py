import base64
import datetime
import hashlib
import io
import random
import socket
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from zoneinfo import ZoneInfo

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

FILE_TYPES = ["xlsx", "xls", "csv"]


# ============================================================
# TIMEZONE
# ============================================================

# Display / application time = India Standard Time
INDIA_TZ = ZoneInfo("Asia/Kolkata")


# ============================================================
# EASY4IP CREDENTIALS
# ============================================================

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

    if "loaded" not in st.session_state:
        st.session_state.loaded = False

    if "uploaded_signature" not in st.session_state:
        st.session_state.uploaded_signature = None

    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = ""

    # ========================================================
    # EDIT STATE
    # ========================================================

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None

    if "edit_candidates" not in st.session_state:
        st.session_state.edit_candidates = []

    if "edit_store_enabled" not in st.session_state:
        st.session_state.edit_store_enabled = False

    if "edit_site_enabled" not in st.session_state:
        st.session_state.edit_site_enabled = False

    if "edit_dvr_enabled" not in st.session_state:
        st.session_state.edit_dvr_enabled = False

    # ========================================================
    # UPDATED FILE STATE
    # ========================================================

    if "file_updated" not in st.session_state:
        st.session_state.file_updated = False

    if "updated_changes" not in st.session_state:
        st.session_state.updated_changes = []

    if "updated_file_name" not in st.session_state:
        st.session_state.updated_file_name = ""

    # ========================================================
    # MONITORING LOG
    # ========================================================

    if "monitor_log" not in st.session_state:
        st.session_state.monitor_log = pd.DataFrame(
            columns=[
                "Date",
                "Time",
                "Store ID",
                "Site Name",
                "DVR Number",
                "Status"
            ]
        )

    if "show_log" not in st.session_state:
        st.session_state.show_log = False

    if "show_updated_file" not in st.session_state:
        st.session_state.show_updated_file = False

    if "load_error" not in st.session_state:
        st.session_state.load_error = ""


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

        clean = clean_column_name(col)

        normalized[clean] = col

    for name in possible_names:

        clean_name = clean_column_name(name)

        if clean_name in normalized:
            return normalized[clean_name]

    return None


# ============================================================
# RESET EDIT STATE
# ============================================================

def reset_edit_state():

    st.session_state.edit_mode = False
    st.session_state.edit_index = None
    st.session_state.edit_candidates = []

    st.session_state.edit_store_enabled = False
    st.session_state.edit_site_enabled = False
    st.session_state.edit_dvr_enabled = False


# ============================================================
# LOAD EXCEL / CSV
# ============================================================

def load_uploaded_file(uploaded_file):

    if uploaded_file is None:
        return False

    try:

        file_name = uploaded_file.name.lower()

        if file_name.endswith(".csv"):

            data = pd.read_csv(
                uploaded_file,
                dtype=str
            )

        else:

            data = pd.read_excel(
                uploaded_file,
                dtype=str
            )

        data = data.dropna(
            axis=1,
            how="all"
        )

        data = data.dropna(
            axis=0,
            how="all"
        )

        data.columns = [
            str(col).strip()
            for col in data.columns
        ]

        # ====================================================
        # STORE ID
        # ====================================================

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

        # ====================================================
        # SITE NAME
        # ====================================================

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

        # ====================================================
        # DVR NUMBER
        # ====================================================

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

        if dvr_column is None:

            st.session_state.load_error = (
                "DVR/P2P column was not found in the uploaded file.\n\n"
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

            st.session_state.loaded = False

            return False

        # ====================================================
        # CREATE CLEAN DATAFRAME
        # ====================================================

        clean_data = pd.DataFrame()

        if store_column is not None:

            clean_data["Store ID"] = (
                data[store_column]
                .fillna("")
                .apply(normalize_serial)
            )

        else:

            clean_data["Store ID"] = ""

        if site_column is not None:

            clean_data["Site Name"] = (
                data[site_column]
                .fillna("")
                .apply(normalize_serial)
            )

        else:

            clean_data["Site Name"] = ""

        clean_data["DVR Number"] = (
            data[dvr_column]
            .fillna("")
            .apply(normalize_serial)
        )

        clean_data["Status"] = "Not Checked"

        clean_data = clean_data[
            clean_data["DVR Number"]
            .astype(str)
            .str.strip()
            != ""
        ].copy()

        clean_data.reset_index(
            drop=True,
            inplace=True
        )

        clean_data = clean_data[
            [
                "Store ID",
                "Site Name",
                "DVR Number",
                "Status"
            ]
        ]

        st.session_state.dvr_data = clean_data

        st.session_state.loaded = True

        st.session_state.load_error = ""

        st.session_state.last_scan_time = None

        st.session_state.scan_completed = 0

        st.session_state.scan_total = 0

        st.session_state.uploaded_file_name = uploaded_file.name

        st.session_state.file_updated = False

        st.session_state.show_updated_file = False

        st.session_state.updated_changes = []

        st.session_state.updated_file_name = ""

        st.session_state.monitor_log = pd.DataFrame(
            columns=[
                "Date",
                "Time",
                "Store ID",
                "Site Name",
                "DVR Number",
                "Status"
            ]
        )

        st.session_state.show_log = False

        reset_edit_state()

        return True

    except Exception as e:

        st.session_state.load_error = (
            "File loading error:\n\n"
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

        st.session_state.loaded = False

        return False


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

        self.sock.settimeout(timeout)

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

        for attempt in range(retries):

            try:

                nonce = random.randrange(
                    2 ** 31
                )

                # IMPORTANT:
                # Easy4IP authentication uses UTC.
                # Do not change this to IST.
                curdate = (
                    datetime.datetime.now(
                        datetime.timezone.utc
                    )
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

                result["headers"][
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

    for token in (
        text
        .replace("\r", " ")
        .replace("\n", " ")
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
            f"{host}:{port} "
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
# ADD MONITORING LOG
# ============================================================

def add_monitor_log(
    index,
    status
):

    try:

        data = st.session_state.dvr_data

        if index not in data.index:
            return

        row = data.loc[index]

        # ====================================================
        # IMPORTANT:
        # Always use India Standard Time for display/log.
        # This works correctly even when Streamlit Cloud
        # server is running in UTC.
        # ====================================================

        now = datetime.datetime.now(
            INDIA_TZ
        )

        new_log = pd.DataFrame(
            [{
                "Date": now.strftime(
                    "%Y-%m-%d"
                ),
                "Time": now.strftime(
                    "%H:%M:%S"
                ),
                "Store ID": normalize_serial(
                    row["Store ID"]
                ),
                "Site Name": normalize_serial(
                    row["Site Name"]
                ),
                "DVR Number": normalize_serial(
                    row["DVR Number"]
                ),
                "Status": status
            }]
        )

        st.session_state.monitor_log = (
            pd.concat(
                [
                    st.session_state.monitor_log,
                    new_log
                ],
                ignore_index=True
            )
        )

    except Exception as e:

        print(
            f"[LOG ERROR] {e}"
        )


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

    # Use IST for application timestamp
    st.session_state.scan_started_at = (
        time.time()
    )

    for index in indexes:

        st.session_state.dvr_data.loc[
            index,
            "Status"
        ] = "Checking..."

    progress = st.progress(
        0
    )

    progress_text = st.empty()

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

            add_monitor_log(
                index,
                status
            )

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

    # ========================================================
    # IMPORTANT:
    # Last scan time is displayed in IST.
    # ========================================================

    st.session_state.last_scan_time = (
        datetime.datetime.now(
            INDIA_TZ
        )
    )

    progress.progress(
        1.0
    )

    progress_text.success(
        "DVR scan completed."
    )


# ============================================================
# DASHBOARD COUNTS
# ============================================================

def get_counts():

    data = st.session_state.dvr_data

    if data is None or data.empty:

        return {
            "total": 0,
            "online": 0,
            "offline": 0
        }

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
        )
    }


# ============================================================
# DARK MODE CSS
# ============================================================

def apply_css():

    st.markdown(
        """
        <style>

        .stApp {
            background-color:#0b1112 !important;
            color:#f5f7f7 !important;
        }

        [data-testid="stAppViewContainer"] {
            background-color:#0b1112 !important;
        }

        [data-testid="stMain"] {
            background-color:#0b1112 !important;
        }

        [data-testid="stHeader"] {
            background-color:#0b1112 !important;
        }

        .main-header {
            background:#007e82 !important;
            color:#ffffff !important;
            padding:22px 30px;
            border-radius:10px;
            margin-bottom:18px;
        }

        .main-title-text {
            color:#ffffff !important;
            font-size:28px;
            font-weight:700;
        }

        .main-subtitle {
            color:#c8eeee !important;
            font-size:13px;
            margin-top:4px;
        }

        .metric-card {
            border-radius:10px;
            padding:18px;
            min-height:110px;
            color:#ffffff !important;
            box-shadow:0 3px 8px rgba(0,0,0,.45);
        }

        .metric-title {
            color:#ffffff !important;
            font-size:13px;
            font-weight:700;
        }

        .metric-value {
            color:#ffffff !important;
            font-size:34px;
            font-weight:700;
            margin-top:10px;
        }

        .metric-total {
            background:#008f91 !important;
        }

        .metric-online {
            background:#168b45 !important;
        }

        .metric-offline {
            background:#c9343d !important;
        }

        .section-box {
            background:#151d1f !important;
            border:1px solid #344143 !important;
            border-radius:10px;
            padding:14px;
            margin-bottom:14px;
        }

        .section-title {
            color:#35d0d0 !important;
            font-size:16px;
            font-weight:700;
            margin-bottom:8px;
        }

        div.stButton > button {
            width:100% !important;
            min-height:40px !important;
            background-color:#263235 !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border:1px solid #526265 !important;
            border-radius:7px !important;
            font-size:14px !important;
            font-weight:700 !important;
            box-shadow:none !important;
        }

        div.stButton > button p {
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            font-weight:700 !important;
        }

        div.stButton > button span {
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
        }

        div.stButton > button:hover {
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            background-color:#304043 !important;
            border-color:#00a7a5 !important;
        }

        div.stButton > button:focus {
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            box-shadow:0 0 0 2px rgba(0,167,165,.35) !important;
        }

        .load-button div.stButton > button {
            background-color:#1769aa !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#1769aa !important;
        }

        .check-button div.stButton > button {
            background-color:#159447 !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#159447 !important;
        }

        .log-button div.stButton > button {
            background-color:#007e82 !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#007e82 !important;
        }

        .edit-button div.stButton > button {
            background-color:#f39c12 !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#f39c12 !important;
        }

        .refresh-button div.stButton > button {
            background-color:#d9363e !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#d9363e !important;
        }

        .save-button div.stButton > button {
            background-color:#159447 !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#159447 !important;
        }

        .cancel-button div.stButton > button {
            background-color:#607d8b !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#607d8b !important;
        }

        .pencil-button div.stButton > button {
            background-color:#f39c12 !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#f39c12 !important;
            min-height:38px !important;
            font-size:16px !important;
        }

        .select-button div.stButton > button {
            background-color:#1769aa !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border-color:#1769aa !important;
        }

        div.stDownloadButton > button {
            background-color:#007e82 !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
            border:1px solid #007e82 !important;
            border-radius:7px !important;
            font-weight:700 !important;
        }

        div.stDownloadButton > button p {
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
        }

        div.stDownloadButton > button span {
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
        }

        div[data-baseweb="input"] {
            background-color:#202a2c !important;
            border:1px solid #46575a !important;
            border-radius:7px !important;
        }

        div[data-baseweb="input"] input {
            background-color:#202a2c !important;
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
        }

        div[data-baseweb="input"] input::placeholder {
            color:#9ba7aa !important;
            -webkit-text-fill-color:#9ba7aa !important;
        }

        div[data-baseweb="input"]:focus-within {
            border:1px solid #00a7a5 !important;
            box-shadow:0 0 0 1px #00a7a5 !important;
        }

        div[data-baseweb="input"] input:disabled {
            background-color:#171f21 !important;
            color:#8d999c !important;
            -webkit-text-fill-color:#8d999c !important;
            opacity:1 !important;
        }

        div[data-baseweb="select"] > div {
            background-color:#202a2c !important;
            border:1px solid #46575a !important;
            color:#ffffff !important;
        }

        div[data-baseweb="select"] span {
            color:#ffffff !important;
        }

        div[data-baseweb="select"] input {
            color:#ffffff !important;
            -webkit-text-fill-color:#ffffff !important;
        }

        div[data-baseweb="popover"] {
            background-color:#171e20 !important;
        }

        ul[role="listbox"] {
            background-color:#171e20 !important;
        }

        li[role="option"] {
            background-color:#171e20 !important;
            color:#ffffff !important;
        }

        li[role="option"]:hover {
            background-color:#263638 !important;
            color:#ffffff !important;
        }

        label {
            color:#d9e1e2 !important;
        }

        label p {
            color:#d9e1e2 !important;
        }

        .stCaption {
            color:#9ba7aa !important;
        }

        section[data-testid="stFileUploaderDropzone"] {
            background-color:#202a2c !important;
            border:1px dashed #526265 !important;
        }

        section[data-testid="stFileUploaderDropzone"] * {
            color:#ffffff !important;
        }

        div[data-testid="stDataFrame"] {
            background-color:#151d1f !important;
            border:1px solid #344143 !important;
            border-radius:8px !important;
            overflow:hidden !important;
        }

        div[data-testid="stDataFrame"] iframe {
            background-color:#151d1f !important;
        }

        [data-testid="stDataFrame"] * {
            scrollbar-color:#46575a #151d1f;
        }

        div[data-testid="stAlert"] {
            border-radius:9px !important;
        }

        .stMarkdown,
        .stMarkdown p,
        .stMarkdown span {
            color:#f1f5f5;
        }

        ::-webkit-scrollbar {
            width:8px;
            height:8px;
        }

        ::-webkit-scrollbar-track {
            background:#101617;
        }

        ::-webkit-scrollbar-thumb {
            background:#46575a;
            border-radius:5px;
        }

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

            <div class="main-title-text">
                📹 DVR LIVE MONITORING
            </div>

            <div class="main-subtitle">
                Automatic P2P DVR monitoring
            </div>

        </div>
        """
    )


# ============================================================
# METRICS
# ============================================================

def render_metrics():

    counts = get_counts()

    cards = [

        (
            "📹 TOTAL DVR",
            counts["total"],
            "metric-total"
        ),

        (
            "✓ ONLINE",
            counts["online"],
            "metric-online"
        ),

        (
            "! OFFLINE",
            counts["offline"],
            "metric-offline"
        )
    ]

    columns = st.columns(3)

    for column, (
        title,
        value,
        css_class
    ) in zip(
        columns,
        cards
    ):

        with column:

            st.html(
                f"""
                <div class="metric-card {css_class}">

                    <div class="metric-title">
                        {title}
                    </div>

                    <div class="metric-value">
                        {value}
                    </div>

                </div>
                """
            )


# ============================================================
# UPDATED EXCEL
# ============================================================

def create_updated_excel():

    output = io.BytesIO()

    data = st.session_state.dvr_data.copy()

    data = data[
        [
            "Store ID",
            "Site Name",
            "DVR Number"
        ]
    ].copy()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        data.to_excel(
            writer,
            index=False,
            sheet_name="DVR Data"
        )

    output.seek(0)

    return output.getvalue()


# ============================================================
# UPDATED CSV
# ============================================================

def create_updated_csv():

    data = st.session_state.dvr_data.copy()

    data = data[
        [
            "Store ID",
            "Site Name",
            "DVR Number"
        ]
    ].copy()

    return data.to_csv(
        index=False
    ).encode("utf-8")


# ============================================================
# CURRENT DVR TABLE DOWNLOAD
# ============================================================

def create_current_excel():

    output = io.BytesIO()

    data = st.session_state.dvr_data.copy()

    data = data[
        [
            "Store ID",
            "Site Name",
            "DVR Number",
            "Status"
        ]
    ].copy()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        data.to_excel(
            writer,
            index=False,
            sheet_name="Current DVR Data"
        )

    output.seek(0)

    return output.getvalue()


def create_current_csv():

    data = st.session_state.dvr_data.copy()

    data = data[
        [
            "Store ID",
            "Site Name",
            "DVR Number",
            "Status"
        ]
    ].copy()

    return data.to_csv(
        index=False
    ).encode("utf-8")


# ============================================================
# UPDATED FILE PANEL
# ============================================================

def render_updated_file():

    if not st.session_state.show_updated_file:
        return

    st.markdown(
        '<div class="section-box">',
        unsafe_allow_html=True
    )

    title_col, close_col = st.columns(
        [9, 1]
    )

    with title_col:

        st.markdown(
            '<div class="section-title">💾 UPDATED FILE</div>',
            unsafe_allow_html=True
        )

    with close_col:

        st.markdown(
            '<div class="cancel-button">',
            unsafe_allow_html=True
        )

        close_updated = st.button(
            "✖",
            key="close_updated_file",
            use_container_width=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    if close_updated:

        st.session_state.show_updated_file = False
        st.session_state.file_updated = False

        st.rerun()

    changes = st.session_state.updated_changes

    if not changes:

        st.info(
            "No changes made."
        )

    else:

        st.success(
            "Changes saved successfully."
        )

        change_data = pd.DataFrame(
            changes
        )

        st.dataframe(
            change_data,
            width="stretch",
            hide_index=True
        )

        st.markdown(
            "**Download updated file:**"
        )

        col1, col2 = st.columns(2)

        with col1:

            excel_bytes = create_updated_excel()

            st.download_button(
                "📥 Download Updated Excel",
                data=excel_bytes,
                file_name=(
                    st.session_state.updated_file_name
                    or "updated_dvr_file.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
                key="download_updated_excel"
            )

        with col2:

            csv_bytes = create_updated_csv()

            st.download_button(
                "📥 Download Updated CSV",
                data=csv_bytes,
                file_name="updated_dvr_file.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_updated_csv"
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
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
        [
            1.15,
            1.35,
            1.25,
            1.25,
            3.0,
            1.25
        ]
    )

    # ========================================================
    # LOAD
    # ========================================================

    with columns[0]:

        st.markdown(
            '<div class="load-button">',
            unsafe_allow_html=True
        )

        with st.popover(
            "📂 Load",
            use_container_width=True
        ):

            uploaded_file = st.file_uploader(
                "Choose DVR file",
                type=FILE_TYPES,
                key="dvr_file_uploader",
                label_visibility="collapsed"
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # ========================================================
    # CHECK ALL
    # ========================================================

    with columns[1]:

        st.markdown(
            '<div class="check-button">',
            unsafe_allow_html=True
        )

        check_clicked = st.button(
            "🌐 Check All",
            use_container_width=True,
            key="toolbar_check",
            disabled=(
                st.session_state.scan_running
                or
                st.session_state.dvr_data.empty
            )
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # ========================================================
    # LOG
    # ========================================================

    with columns[2]:

        st.markdown(
            '<div class="log-button">',
            unsafe_allow_html=True
        )

        log_clicked = st.button(
            "📝 Log",
            use_container_width=True,
            key="toolbar_log",
            disabled=(
                st.session_state.dvr_data.empty
            )
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # ========================================================
    # REFRESH
    # ========================================================

    with columns[3]:

        st.markdown(
            '<div class="refresh-button">',
            unsafe_allow_html=True
        )

        refresh_clicked = st.button(
            "🔄 Refresh",
            use_container_width=True,
            key="toolbar_refresh",
            disabled=(
                st.session_state.scan_running
                or
                st.session_state.dvr_data.empty
            )
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # ========================================================
    # SPACER
    # ========================================================

    with columns[4]:

        st.write("")

    # ========================================================
    # UPDATED FILE BUTTON
    # ========================================================

    with columns[5]:

        if st.session_state.file_updated:

            st.markdown(
                '<div class="download-button">',
                unsafe_allow_html=True
            )

            updated_clicked = st.button(
                "💾 Updated File",
                use_container_width=True,
                key="toolbar_updated_file"
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        else:

            updated_clicked = False

    # ========================================================
    # ACTIONS
    # ========================================================

    if check_clicked:

        run_check_all()

        st.rerun()

    if refresh_clicked:

        run_check_all()

        st.rerun()

    if log_clicked:

        st.session_state.show_log = True

        st.rerun()

    if updated_clicked:

        st.session_state.show_updated_file = True

        st.rerun()

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    return uploaded_file


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
            5.5,
            1.5,
            1.2
        ]
    )

    # ========================================================
    # SEARCH
    # ========================================================

    with columns[0]:

        search = st.text_input(
            "Search",
            placeholder=(
                "Store ID, Site Name or DVR Number"
            ),
            key="search_text"
        )

    # ========================================================
    # STATUS
    # ========================================================

    with columns[1]:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Online",
                "Offline"
            ],
            key="status_filter"
        )

    # ========================================================
    # EDIT
    # ========================================================

    with columns[2]:

        if st.session_state.edit_mode:

            st.markdown(
                '<div class="cancel-button">',
                unsafe_allow_html=True
            )

            close_edit_clicked = st.button(
                "✖ Close Edit",
                use_container_width=True,
                key="search_close_edit"
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

            edit_clicked = False

        else:

            st.markdown(
                '<div class="edit-button">',
                unsafe_allow_html=True
            )

            edit_clicked = st.button(
                "✏️ Edit",
                use_container_width=True,
                key="search_edit",
                disabled=(
                    st.session_state.dvr_data.empty
                )
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

            close_edit_clicked = False

    # ========================================================
    # CLOSE EDIT
    # ========================================================

    if close_edit_clicked:

        reset_edit_state()

        st.rerun()

    # ========================================================
    # EDIT CLICK
    # ========================================================

    if edit_clicked:

        query = normalize_serial(
            search
        ).strip().lower()

        if not query:

            reset_edit_state()

            st.warning(
                "Enter Store ID, Site Name or DVR Serial Number in Search first."
            )

        else:

            data = (
                st.session_state.dvr_data
                .copy()
            )

            exact_matches = data[
                data["Store ID"]
                .apply(normalize_serial)
                .str.lower()
                .eq(query)
                |
                data["Site Name"]
                .apply(normalize_serial)
                .str.lower()
                .eq(query)
                |
                data["DVR Number"]
                .apply(normalize_serial)
                .str.lower()
                .eq(query)
            ]

            if len(exact_matches) == 1:

                st.session_state.edit_index = (
                    exact_matches.index[0]
                )

                st.session_state.edit_mode = True

                st.session_state.edit_candidates = []

                st.session_state.edit_store_enabled = False
                st.session_state.edit_site_enabled = False
                st.session_state.edit_dvr_enabled = False

                st.rerun()

            elif len(exact_matches) > 1:

                st.session_state.edit_mode = True

                st.session_state.edit_index = None

                st.session_state.edit_candidates = (
                    exact_matches.index.tolist()
                )

                st.rerun()

            else:

                searchable = (
                    data["Store ID"]
                    .apply(normalize_serial)
                    .str.lower()
                    + " "
                    +
                    data["Site Name"]
                    .apply(normalize_serial)
                    .str.lower()
                    + " "
                    +
                    data["DVR Number"]
                    .apply(normalize_serial)
                    .str.lower()
                )

                partial_matches = data[
                    searchable.str.contains(
                        query,
                        na=False,
                        regex=False
                    )
                ]

                if partial_matches.empty:

                    reset_edit_state()

                    st.error(
                        "No matching DVR found."
                    )

                elif len(partial_matches) == 1:

                    st.session_state.edit_index = (
                        partial_matches.index[0]
                    )

                    st.session_state.edit_mode = True

                    st.session_state.edit_candidates = []

                    st.session_state.edit_store_enabled = False
                    st.session_state.edit_site_enabled = False
                    st.session_state.edit_dvr_enabled = False

                    st.rerun()

                else:

                    st.session_state.edit_mode = True

                    st.session_state.edit_index = None

                    st.session_state.edit_candidates = (
                        partial_matches.index.tolist()
                    )

                    st.rerun()

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    return search, status_filter


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

    search = (
        search or ""
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
                na=False,
                regex=False
            )
        ]

    if status_filter != "All":

        data = data[
            data["Status"]
            == status_filter
        ]

    return data


# ============================================================
# STATUS STYLE
# ============================================================

def style_status(value):

    if value == "Online":

        return (
            "color:#21d66b;"
            "font-weight:bold;"
        )

    if value == "Offline":

        return (
            "color:#ff5964;"
            "font-weight:bold;"
        )

    if value == "Checking...":

        return (
            "color:#4aa3ff;"
            "font-weight:bold;"
        )

    return (
        "color:#9ba7aa;"
        "font-weight:bold;"
    )


# ============================================================
# EDIT PANEL
# ============================================================

def render_edit():

    if not st.session_state.edit_mode:
        return

    st.markdown(
        '<div class="section-box">',
        unsafe_allow_html=True
    )

    title_col, close_col = st.columns(
        [9, 1]
    )

    with title_col:

        st.markdown(
            '<div class="section-title">✏️ EDIT DVR</div>',
            unsafe_allow_html=True
        )

    with close_col:

        st.markdown(
            '<div class="cancel-button">',
            unsafe_allow_html=True
        )

        close_clicked = st.button(
            "✖",
            key="close_edit_panel",
            use_container_width=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    if close_clicked:

        reset_edit_state()

        st.rerun()

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

    # ========================================================
    # MULTIPLE MATCHES
    # ========================================================

    candidates = (
        st.session_state.get(
            "edit_candidates",
            []
        )
    )

    if (
        st.session_state.edit_index is None
        and candidates
    ):

        st.warning(
            "Multiple DVRs found. Select the DVR you want to edit."
        )

        options = []

        option_to_index = {}

        for index in candidates:

            row = data.loc[index]

            label = (
                f"Store ID: "
                f"{normalize_serial(row['Store ID']) or '-'}"
                f" | "
                f"Site: "
                f"{normalize_serial(row['Site Name']) or '-'}"
                f" | "
                f"DVR: "
                f"{normalize_serial(row['DVR Number'])}"
            )

            options.append(label)

            option_to_index[label] = index

        selected = st.selectbox(
            "Select DVR",
            options,
            key="edit_selected_dvr"
        )

        st.markdown(
            '<div class="select-button">',
            unsafe_allow_html=True
        )

        select_clicked = st.button(
            "Select DVR",
            use_container_width=True,
            key="select_edit_dvr"
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

        if select_clicked:

            st.session_state.edit_index = (
                option_to_index[selected]
            )

            st.session_state.edit_candidates = []

            st.session_state.edit_store_enabled = False
            st.session_state.edit_site_enabled = False
            st.session_state.edit_dvr_enabled = False

            st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        return

    # ========================================================
    # SELECTED DVR
    # ========================================================

    selected_index = (
        st.session_state.edit_index
    )

    if (
        selected_index is None
        or selected_index not in data.index
    ):

        st.info(
            "Use the Search box above and click ✏️ Edit."
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        return

    row = data.loc[
        selected_index
    ]

    st.success(
        "DVR found. Edit the details below."
    )

    # ========================================================
    # CURRENT VALUES
    # ========================================================

    current_col1, current_col2, current_col3 = (
        st.columns(3)
    )

    with current_col1:

        st.caption(
            "Current Store ID"
        )

        st.write(
            normalize_serial(
                row["Store ID"]
            )
            or "-"
        )

    with current_col2:

        st.caption(
            "Current Site Name"
        )

        st.write(
            normalize_serial(
                row["Site Name"]
            )
            or "-"
        )

    with current_col3:

        st.caption(
            "Current DVR Serial"
        )

        st.write(
            normalize_serial(
                row["DVR Number"]
            )
            or "-"
        )

    st.markdown(
        "**Enter New Values**"
    )

    # ========================================================
    # STORE ID
    # ========================================================

    store_col, store_pencil = st.columns(
        [10, 1]
    )

    with store_col:

        new_store_id = st.text_input(
            "Store ID",
            value=normalize_serial(
                row["Store ID"]
            ),
            key=f"edit_store_value_{selected_index}",
            disabled=(
                not st.session_state.edit_store_enabled
            )
        )

    with store_pencil:

        st.markdown(
            '<div class="pencil-button">',
            unsafe_allow_html=True
        )

        store_edit_clicked = st.button(
            "✏️",
            key=f"pencil_store_{selected_index}",
            use_container_width=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    if store_edit_clicked:

        st.session_state.edit_store_enabled = True

        st.rerun()

    # ========================================================
    # SITE NAME
    # ========================================================

    site_col, site_pencil = st.columns(
        [10, 1]
    )

    with site_col:

        new_site_name = st.text_input(
            "Site Name",
            value=normalize_serial(
                row["Site Name"]
            ),
            key=f"edit_site_value_{selected_index}",
            disabled=(
                not st.session_state.edit_site_enabled
            )
        )

    with site_pencil:

        st.markdown(
            '<div class="pencil-button">',
            unsafe_allow_html=True
        )

        site_edit_clicked = st.button(
            "✏️",
            key=f"pencil_site_{selected_index}",
            use_container_width=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    if site_edit_clicked:

        st.session_state.edit_site_enabled = True

        st.rerun()

    # ========================================================
    # DVR SERIAL
    # ========================================================

    dvr_col, dvr_pencil = st.columns(
        [10, 1]
    )

    with dvr_col:

        new_dvr_number = st.text_input(
            "DVR Serial Number",
            value=normalize_serial(
                row["DVR Number"]
            ),
            key=f"edit_dvr_value_{selected_index}",
            disabled=(
                not st.session_state.edit_dvr_enabled
            )
        )

    with dvr_pencil:

        st.markdown(
            '<div class="pencil-button">',
            unsafe_allow_html=True
        )

        dvr_edit_clicked = st.button(
            "✏️",
            key=f"pencil_dvr_{selected_index}",
            use_container_width=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    if dvr_edit_clicked:

        st.session_state.edit_dvr_enabled = True

        st.rerun()

    st.write("")

    # ========================================================
    # SAVE / CANCEL
    # ========================================================

    save_col, cancel_col = st.columns(
        [1, 1]
    )

    with save_col:

        st.markdown(
            '<div class="save-button">',
            unsafe_allow_html=True
        )

        save_clicked = st.button(
            "💾 Save Changes",
            use_container_width=True,
            key="save_edit_dvr"
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with cancel_col:

        st.markdown(
            '<div class="cancel-button">',
            unsafe_allow_html=True
        )

        cancel_clicked = st.button(
            "✖ Close Edit",
            use_container_width=True,
            key="cancel_edit_dvr"
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # ========================================================
    # SAVE
    # ========================================================

    if save_clicked:

        old_store_id = normalize_serial(
            row["Store ID"]
        )

        old_site_name = normalize_serial(
            row["Site Name"]
        )

        old_dvr_number = normalize_serial(
            row["DVR Number"]
        )

        new_store_id = normalize_serial(
            new_store_id
        )

        new_site_name = normalize_serial(
            new_site_name
        )

        new_dvr_number = normalize_serial(
            new_dvr_number
        )

        if not new_dvr_number:

            st.error(
                "DVR Serial Number is required."
            )

            return

        changes = []

        if old_store_id != new_store_id:

            changes.append(
                {
                    "Field": "Store ID",
                    "Old Value": old_store_id or "-",
                    "New Value": new_store_id or "-"
                }
            )

        if old_site_name != new_site_name:

            changes.append(
                {
                    "Field": "Site Name",
                    "Old Value": old_site_name or "-",
                    "New Value": new_site_name or "-"
                }
            )

        if old_dvr_number != new_dvr_number:

            changes.append(
                {
                    "Field": "DVR Serial Number",
                    "Old Value": old_dvr_number or "-",
                    "New Value": new_dvr_number or "-"
                }
            )

        if not changes:

            st.warning(
                "No changes were made."
            )

            return

        # ====================================================
        # UPDATE DATA
        # ====================================================

        st.session_state.dvr_data.loc[
            selected_index,
            "Store ID"
        ] = new_store_id

        st.session_state.dvr_data.loc[
            selected_index,
            "Site Name"
        ] = new_site_name

        st.session_state.dvr_data.loc[
            selected_index,
            "DVR Number"
        ] = new_dvr_number

        st.session_state.dvr_data.loc[
            selected_index,
            "Status"
        ] = "Not Checked"

        # ====================================================
        # UPDATED FILE
        # ====================================================

        st.session_state.file_updated = True

        st.session_state.show_updated_file = True

        st.session_state.updated_changes = changes

        original_name = (
            st.session_state.uploaded_file_name
            or "DVR_File.xlsx"
        )

        if "." in original_name:

            base_name = (
                original_name.rsplit(
                    ".",
                    1
                )[0]
            )

        else:

            base_name = original_name

        st.session_state.updated_file_name = (
            f"{base_name}_UPDATED.xlsx"
        )

        reset_edit_state()

        st.rerun()

    # ========================================================
    # CLOSE EDIT
    # ========================================================

    if cancel_clicked:

        reset_edit_state()

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# MONITORING LOG
# ============================================================

def render_monitor_log():

    if not st.session_state.show_log:
        return

    st.markdown(
        '<div class="section-box">',
        unsafe_allow_html=True
    )

    title_col, close_col = st.columns(
        [9, 1]
    )

    with title_col:

        st.markdown(
            '<div class="section-title">📝 ONLINE / OFFLINE LOG</div>',
            unsafe_allow_html=True
        )

    with close_col:

        st.markdown(
            '<div class="cancel-button">',
            unsafe_allow_html=True
        )

        close_log_clicked = st.button(
            "✖",
            key="close_log",
            use_container_width=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    if close_log_clicked:

        st.session_state.show_log = False

        st.rerun()

    log_data = st.session_state.monitor_log

    if log_data.empty:

        st.info(
            "No Online / Offline log available yet. "
            "Run Check All or Refresh."
        )

    else:

        st.caption(
            f"Total log entries: {len(log_data)}"
        )

        st.dataframe(
            log_data.iloc[::-1],
            width="stretch",
            height=350,
            hide_index=True
        )

        log_csv = log_data.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download Online / Offline Log",
            data=log_csv,
            file_name=(
                "DVR_Online_Offline_Log.csv"
            ),
            mime="text/csv",
            use_container_width=True,
            key="download_monitor_log"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
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

    # ========================================================
    # TABLE TITLE + DOWNLOAD
    # ========================================================

    title_col, download_col = st.columns(
        [7, 3]
    )

    with title_col:

        st.markdown(
            '<div class="section-title">DVR LIST</div>',
            unsafe_allow_html=True
        )

    with download_col:

        download_excel = create_current_excel()

        st.download_button(
            "📥 Download Current DVR Table",
            data=download_excel,
            file_name="Current_DVR_Table.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            key="download_current_dvr_excel"
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
            subset=["Status"]
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
# AUTO REFRESH
# ============================================================

def auto_refresh():

    refresh_count = st_autorefresh(
        interval=(
            AUTO_REFRESH_SECONDS * 1000
        ),
        key="dvr_auto_refresh"
    )

    return refresh_count


# ============================================================
# MAIN
# ============================================================

def main():

    apply_css()

    render_header()

    render_metrics()

    st.write("")

    # ========================================================
    # CONTROL PANEL
    # ========================================================

    uploaded_file = render_toolbar()

    # ========================================================
    # LOAD FILE
    # ========================================================

    if uploaded_file is not None:

        uploaded_signature = (
            uploaded_file.name,
            uploaded_file.size
        )

        if (
            st.session_state.get(
                "uploaded_signature"
            )
            != uploaded_signature
        ):

            if load_uploaded_file(
                uploaded_file
            ):

                st.session_state.uploaded_signature = (
                    uploaded_signature
                )

                st.rerun()

    # ========================================================
    # LOAD ERROR
    # ========================================================

    if st.session_state.load_error:

        st.error(
            st.session_state.load_error
        )

    # ========================================================
    # NO FILE
    # ========================================================

    if (
        not st.session_state.loaded
        or
        st.session_state.dvr_data.empty
    ):

        st.info(
            "📂 Load an Excel / CSV DVR file above to start monitoring."
        )

        auto_refresh()

        return

    # ========================================================
    # AUTOMATIC REFRESH
    # ========================================================

    refresh_count = auto_refresh()

    if (
        refresh_count > 0
        and
        not st.session_state.scan_running
        and
        not st.session_state.dvr_data.empty
        and
        st.session_state.get(
            "last_auto_refresh_count"
        ) != refresh_count
    ):

        st.session_state.last_auto_refresh_count = (
            refresh_count
        )

        run_check_all()

    # ========================================================
    # SEARCH
    # ========================================================

    search, status_filter = render_search()

    # ========================================================
    # PROGRESS
    # ========================================================

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
            f"Checking {completed} / {total} DVRs "
            f"({int(percent * 100)}%)"
        )

    elif st.session_state.last_scan_time is not None:

        # ====================================================
        # DISPLAY LAST SCAN IN IST
        # ====================================================

        st.caption(
            "Last scan: "
            +
            st.session_state.last_scan_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            +
            " IST"
        )

    else:

        st.caption(
            f"Ready • Automatic scan every "
            f"{AUTO_REFRESH_SECONDS} seconds"
        )

    # ========================================================
    # EDIT
    # ========================================================

    render_edit()

    # ========================================================
    # UPDATED FILE
    # ========================================================

    render_updated_file()

    # ========================================================
    # TABLE
    # ========================================================

    filtered_data = filter_data(
        search,
        status_filter
    )

    render_table(
        filtered_data
    )

    # ========================================================
    # LOG
    # ========================================================

    render_monitor_log()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
