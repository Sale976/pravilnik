import streamlit as st
import re, os, time
import json
from pathlib import Path
from datetime import datetime
import socket
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


st.set_page_config(
    page_title="Pretraga PoPV - PoTP",
    layout="wide"
)

# Google Sheets API scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Authenticate with credentials stored in Streamlit secrets
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["google_service_account"], scope
)
gc = gspread.authorize(credentials)

# Open your Google Sheet by name (change "VisitorLog" to your sheet name)
sheet = gc.open("logs_file").sheet1

def log_visit(count):
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    ip = "unknown"  # Replace with actual IP if needed
    try:
        sheet.append_row([timestamp, count, ip])
        #st.write("✅ Visit logged:", timestamp, count, ip)
    except Exception as e:
        st.error(f"❌ Failed to log visit: {e}")


st.markdown("""
    <style>
    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #ADD8E6;
    }
    /* Remove default top padding inside sidebar */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0rem;
    }

    /* Optional: reduce padding/margin of your content */
    .sidebar-top {
        margin-top: -5.5rem;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)


# --- Config ---
COUNTER_FILE = Path("data/visitor_counter.json")
COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)

# --- Load or create the counter ---
def load_counter():
    path = Path(COUNTER_FILE)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f).get("count", 0)
    else:
        return 0

# --- Save counter back to file ---
def save_counter(count):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"count": count}, f)

def reset_counter():
    save_counter(0)
    st.session_state.counted = False  # allow recount in session


def get_ip():
    try:
        # Fallback IP method (not always accurate on cloud)
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "unknown"

# --- Increment the counter only once per session ---
if "counted" not in st.session_state:
    count = load_counter() + 1
    save_counter(count)
    log_visit(count)  # 👈 CALL IT HERE
    st.session_state.counted = True
else:
    count = load_counter()

# --- Show counter in sidebar with st.metric ---
st.sidebar.markdown("#### 👥 Brojač Posetilaca")
st.sidebar.markdown(f'<div style="font-size: 30px;"><strong>{count}</strong></div>', unsafe_allow_html=True)
st.sidebar.write(f"Hvala na poseti!")
st.sidebar.write("---")
#st.sidebar.write("")

with st.sidebar.expander("ℹ️ Uputstvo"):
    st.markdown("""
    - Unesite ključnu reč ili frazu za pretragu.
    - Pri unosu reči ne koristiti kvačice iznad slova.
    - Kliknite na PDF ikonicu da otvorite dokument.
    """)

search_mode = st.sidebar.radio(
    "Način pretrage:",
    ["Tačna fraza", "Bilo koja reč"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.write(f"📄 Verzija: v1.1.2")
st.markdown("""
    <style>
    div[data-testid="stSidebar"] > div:first-child {
        position: relative;
    }
    .bottom-sidebar {
        position: absolute;
        bottom: 0px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown(
    '<div class="bottom-sidebar">Made by: Aleksandar</div>',
    unsafe_allow_html=True
)
#st.sidebar.markdown("🔧 *Autor: Aleksandar P.*")

#st.sidebar.markdown("[💬 Prijavite grešku](mailto:aca1976@mts.rs)")
    
# --- Title and Description ---
st.markdown(
    """
    <h2 style='text-align: center; font-size:28px;'>
        Web aplikacija za pretragu Pravilnika o Podeli Vozila (PoPV) i Pravilnika o Tehničkom Pregledu (PoTP)
    </h2>
    <p style='font-size:18px; text-align: left;'>
        🛈 Aplikacija pretražuje tekstualni fajl koji prikazuje broj člana i stranu iz PDF verzije pravilnika.
        Brojevi stranica važe ako su PDF fajlovi preuzeti sa zvaničnog izvora (PIS) bez izmene.
    </p>
    </h2>
    <p style='font-size:18px; text-align: justify;'>
        🛈 Pravilnik o Podeli Vozila, <b>br. 53 од 20. јуна 2025.</b>  |  Pravilnik o Tehničkom Pregledu, <b>br. 62 od 26. маја 2022.</b> 
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# --- Session State ---
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

def clear_search():
    st.session_state.search_query = ""

# --- File path ---
file_path = "pravilnik.txt"

# --- Create demo file if not exist ---
try:
    with open(file_path, "x", encoding="utf-8") as f:
        f.write("ABS (kočenje) -- Član 30 (PoPV) str. 35\n")
        f.write("Pregled svetala -- Član 12 (PoTP) str. 15\n")
        f.write("Ovaj red ne sadrži ništa relevantno.\n")
except FileExistsError:
    pass

# --- Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.text_input(
        r"$\textsf{\large Unesite tekst za pretragu:}$",
        value=st.session_state.search_query,
        key="search_query"
    )
    st.button("Obrišite rezultate pretrage", on_click=clear_search)

with col2:
    st.markdown("<div style='margin-top: 32px;'>", unsafe_allow_html=True)

    matching_lines = []

    if st.session_state.search_query:
        query = st.session_state.search_query.lower()
        words = query.split()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_lower = line.lower()

                    # --- Search Logic based on mode ---
                    match_found = False
                    if search_mode == "Tačna fraza":
                        match_found = query in line_lower
                    elif search_mode == "Bilo koja reč":
                        match_found = any(word in line_lower for word in words)

                    if match_found:
                        highlighted = line.strip()
                        if search_mode == "Tačna fraza":
                            highlighted = re.sub(
                                f"({re.escape(query)})",
                                r"<mark>\1</mark>",
                                highlighted,
                                flags=re.IGNORECASE
                            )
                        else:
                            for word in words:
                                highlighted = re.sub(
                                    f"({re.escape(word)})",
                                    r"<mark>\1</mark>",
                                    highlighted,
                                    flags=re.IGNORECASE
                                )

                        matching_lines.append(highlighted)
        except FileNotFoundError:
            st.error(f"Greška: Fajl '{file_path}' nije pronađen.")


        if matching_lines:
            st.markdown(
                "<h3 style='color: #0077b6; margine-top: -20px; font-size: 20px;'>🔍 Rezultati pretrage:</h3>",
                unsafe_allow_html=True
            )

            for match in matching_lines:
                acronym_match = re.search(r"\((PoPV|PoTP)\)", match)
                page_match = re.search(r"[Ss]tr\.*\s*(\d+)", match)

                acronym = acronym_match.group(1) if acronym_match else None
                page_number = page_match.group(1) if page_match else None

                file_link = ""
                if acronym and page_number:
                    # GitHub-hosted PDFs via jsDelivr
                    pdf_links = {
                        "PoPV": "https://cdn.jsdelivr.net/gh/Sale976/pravilnik/popv.pdf",
                        "PoTP": "https://cdn.jsdelivr.net/gh/Sale976/pravilnik/potp.pdf"
                    }
                    pdf_url = pdf_links.get(acronym)
                    if pdf_url:
                        full_url = f"{pdf_url}#page={page_number}"
                        file_link = (
                            f"<a href='{full_url}' target='_blank' "
                            f"title='Otvori PDF na strani {page_number}' "
                            f"style='color:#0077b6; font-weight: bold; text-decoration: none;'>"
                            f"📄 Pravilnik u PDF-u</a>"
                        )

                st.markdown(
                    f"""
                    <div style='display: flex; flex-direction: row; align-items: center;
                                gap: 10px; padding: 5px; background-color: #B9F1C0;
                                border-left: 4px solid #0077b6; margin-bottom: 5px;
                                font-size:17px; flex-wrap: wrap;'>
                        <div>{match}</div>
                        <div>{file_link}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Nisu pronađeni odgovarajući rezultati.")
    else:
        st.info("")

    st.markdown("</div>", unsafe_allow_html=True)
