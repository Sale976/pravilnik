import streamlit as st
import base64
import re
import json
from pathlib import Path
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import string
import snowballstemmer


st.set_page_config(
    page_title="Pretraga PPMV & PTPV",
    page_icon="📘",
    layout="wide"
)


# Google Sheets API scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Authenticate with credentials stored in Streamlit secrets
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["google_service_account"], scope
)
gc = gspread.authorize(credentials)

# Open your Google Sheet (change "logs_file" if needed)
# sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1jXw517eCBbEWvhgJ3uxxASnTZ5kdqyWZT0e9ke-KQ4U/edit?gid=0#gid=0").worksheet("logs")

# --- Config ---
COUNTER_FILE = Path("data/visitor_counter.json")
COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)


# --- CSS STYLES ---
st.markdown("""
    <style>
    /* Main sidebar container with fixed height */
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #ADD8E6;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }
    
    /* Container for the top content */
    .sidebar-top {
        flex-shrink: 0;
    }
    
    /* Container for the bottom content - FIXED POSITIONING */
    .sidebar-bottom-container {
        margin-top: auto;
        position: sticky;
        bottom: 0;
        width: 100%;
    }
    
    .sidebar-bottom {
        position: fixed;
        bottom: 1.2rem;
        left: 1.2rem;
        right: 1.2rem;
        width: 15rem;
        background-color: #f8f9fa;
        border-top: 3px solid #0077b6;
        border-radius: 8px 8px 8px 8px;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.5);
        font-size: 14px;
        padding: 5px 12px;
    }

    /* Your original styles for the expandable details section */
    .sidebar-bottom details summary {
        cursor: pointer;
        font-size: 15px;
        list-style: none; /* Removes the default triangle */
    }
    
    .sidebar-bottom details[open] div {
        animation: expandUp 0.1s ease-in-out;
    }

    @keyframes expandUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    
    /* Custom styling for the main content */
    .main-content {
        padding: 2rem;
    }
    
    .search-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .results-table {
        margin-top: 20px;
    }
    
    .highlight {
        background-color: #fff8e1;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    /* Logo styling */
    .logo {
        text-align: center;
        margin-bottom: 20px;
        font-size: 24px;
        font-weight: bold;
        color: #0077b6;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTENT ---
with st.sidebar:
    # Logo at the top
    # st.markdown('<div class="logo">📘 Pretraga Pravilnika</div>', unsafe_allow_html=True)
    st.image("./data/inspect.jpg", width=240)
    #st.image("https://inspektlabs.com/blog/content/images/2020/09/Pre-Purchase_Inspection_Preview-3.jpg", width=240)
    
    # Container for top elements
    st.markdown('<div class="sidebar-top">', unsafe_allow_html=True)
    
    # --- TOP ELEMENTS ---
    with st.expander("ℹ️ Uputstvo", expanded=True):
        st.markdown("""
        - Unesite ključnu reč ili frazu za pretragu.  
        - Pri unosu reči ne koristiti kvačice iznad slova.  
        - Kliknite na PDF ikonicu da otvorite dokument.  
        """)

    search_mode = st.radio(
        "Način pretrage:",
        ["Tačna fraza", "Bilo koja reč"],
        index=0
    )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close top container

    # Spacer to push content to bottom
    st.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True)

    # ------------------------------------------------------------

    # CSS ZA FIKSNO POZICIONIRANJE (Ignoriše logo i ostalo)
    st.markdown("""
        <style>
            /* Ciljamo PRVO dugme u sidebar-u i fiksiramo ga za ekran */
            section[data-testid="stSidebar"] .stButton:nth-of-type(1) button {
                position: fixed;
                top: 20px;        /* 10px od samog vrha stranice */
                left: 44px;       /* 10px od leve ivice ekrana/sidebar-a */
                z-index: 999999;  /* Ide iznad logoa i svega ostalog */
                width: auto;
                padding: 2px 10px !important;
                height: auto;
                min-height: 0px;
            }

            /* Opciono: Ako logo previše "beži" gore, dodajemo razmak */
            [data-testid="stSidebarContent"] {
                padding-top: 1rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # DEFINICIJA MODALA
    @st.dialog("Pregled fajla", width="large")
    def prikazi_fajl_modal(putanja):
        try:
            with open(putanja, "r", encoding="utf-8") as f:
                sadrzaj = f.read()
            st.text_area("Sadržaj dokumenta:", value=sadrzaj, height=700, disabled=True)
            if st.button("Zatvori"):
                st.rerun()
        except FileNotFoundError:
            st.error("Fajl nije pronađen.")

    # SIDEBAR POZICIONIRANJE
    with st.sidebar:
        # Koristimo st.html da bi ID sigurno bio prihvaćen
        st.html('<div id="moje-dugme-kontejner">')
        if st.button("📄 Otvori Tekstualni fajl"):
            prikazi_fajl_modal("pravilnik_1.txt")
        st.html('</div>')
    
        # Dodajemo prazan prostor (spacer) da ostali elementi ne odu pod dugme
        st.markdown("<br><br>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    
    # --- BOTTOM ELEMENT ---
    # This markdown block with the "sidebar-bottom" class will be pushed down
    st.markdown('<div class="sidebar-bottom-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sidebar-bottom">
            <details>
                <summary><strong>ℹ️ O Aplikaciji</strong></summary>
                <div>
                    <b>Web aplikacija za pretragu Pravilnika (PPMV, PTPV)</b><br><br>
                    🔍 Omogućava brzo pronalaženje članova i stranica u pravilnicima.<br><br>
                    📄 Klikom na link otvarate odgovarajući PDF fajl na traženoj stranici.<br><br>
                    👨‍💻 Autor: <b>AI & Aleksandar</b><br>
                    📄 Verzija: <b>v1.5</b><br>
                    🛠️ Izrađeno pomoću <a href="https://streamlit.io" target="_blank">Streamlit</a>
                </div>
            </details>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


#st.sidebar.markdown("[💬 Prijavite grešku](mailto:aca1976@mts.rs)")
    
# --- Title and Description ---
st.markdown(
    """
    <h2 style='text-align: center; font-size:28px;'>
        Web aplikacija za pretragu Pravilnika o Podeli Motornih Vozila (PPMV) i Pravilnika o Tehničkom Pregledu Vozila (PTPV)
    </h2>
    <p style='font-size:18px; text-align: left;'>
        🛈 Aplikacija pretražuje tekstualni fajl i na osnovu pretrage prikazuje broj člana i stranu iz PDF verzije pravilnika. Brojevi stranica važe ako su PDF fajlovi preuzeti sa zvaničnog izvora (PIS) bez izmena.<br>
        🛈 Tekstualni fajl (gornje levo dugme za prikaz sadržaja) je za korisnika aplikacije isključivo informativnog karaktera!
    </p>
    </h2>
    <p style='font-size:18px; text-align: justify;'>
        🛈 Pravilnik o Podeli Motornih i Priključnih Vozila, <b>br. 53 од 20. јуна 2025.</b>&#160; &#160; &#160;|&#160; &#160; &#160;Pravilnik o Tehničkom Pregledu Vozila, <b>br. 62 od 26. маја 2022.</b> 
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
file_path = "pravilnik_1.txt"

# --- Create demo file if not exist ---
try:
    with open(file_path, "x", encoding="utf-8") as f:
        f.write("ABS (kočenje) -- Član 30 (PPMV) str. 35\n")
        f.write("Pregled svetala -- Član 12 (PTPV) str. 15\n")
        f.write("Ovaj red ne sadrži ništa relevantno.\n")
except FileExistsError:
    pass

# --- Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    # CSS koji pomera sadržaj nadole za onoliko piksela koliko je potrebno
    st.markdown(
        """
        <style>
            div[data-testid="stVerticalBlock"] > div:has(input[key="search_query"]) {
                margin-top: -10px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.text_input(
        r"$\textsf{\large Unesite tekst za pretragu:}$",
        value=st.session_state.search_query,
        key="search_query"
    )
    st.button("Obrišite rezultate pretrage", on_click=clear_search)


# --- Stemmer setup ---
stemmer = snowballstemmer.stemmer("serbian")

def clean_and_tokenize(text):
    """Remove punctuation and split to words."""
    return text.translate(str.maketrans('', '', string.punctuation)).lower().split()

def stem_words(word_list):
    """Return list of stemmed lowercase words."""
    return [stemmer.stemWord(word.lower()) for word in word_list]

def find_words_by_stem(stem_target, line_words):
    """Return list of words in line matching the target stem."""
    return [word for word in line_words if stemmer.stemWord(word.lower()) == stem_target]

with col2:
    st.markdown("<div style='margin-top: 0px;'>", unsafe_allow_html=True)

    matching_lines = []

    if st.session_state.search_query:
        query = st.session_state.search_query.lower()
        words = query.split()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_clean = line.strip()
                    words_in_line = clean_and_tokenize(line_clean)
                    
                    match_found = False
                    
                    if search_mode == "Tačna fraza":
                        # Exact phrase using word boundaries
                        pattern = r'\b' + re.escape(query.lower()) + r'\b'
                        match_found = re.search(pattern, line_clean.lower())
                    
                    elif search_mode == "Bilo koja reč":
                        # Match stemmed forms
                        query_stems = stem_words(words)
                        line_stems = stem_words(words_in_line)
                        match_found = any(qs in line_stems for qs in query_stems)
                        
                    if match_found:
                        highlighted = line_clean
                        
                        if search_mode == "Tačna fraza":
                            # Highlight exact phrase
                            highlighted = re.sub(
                                f"\\b({re.escape(query)})\\b",
                                r"<mark>\1</mark>",
                                highlighted,
                                flags=re.IGNORECASE
                            )
                        else:
                            # Highlight each word in line that matches query stems
                            for qword in words:
                                qstem = stemmer.stemWord(qword.lower())
                                matches = find_words_by_stem(qstem, words_in_line)
                                for actual_word in set(matches):
                                    highlighted = re.sub(
                                        f"\\b({re.escape(actual_word)})\\b",
                                        r"<mark>\1</mark>",
                                        highlighted,
                                        flags=re.IGNORECASE
                                    )
                                    
                        matching_lines.append(highlighted)
        except FileNotFoundError:
            st.error(f"Greška: Fajl '{file_path}' nije pronađen.")
        
        if matching_lines:
            st.markdown(
                "<h3 style='color: #0077b6; margin-top: -19px; font-size: 17px;'>🔍 Rezultati pretrage:</h3>",
                unsafe_allow_html=True
            )
            for match in matching_lines:
                acronym_match = re.search(r"\((PPMV|PTPV)\)", match)
                page_match = re.search(r"[Ss]tr\.*\s*(\d+)", match)
                
                acronym = acronym_match.group(1) if acronym_match else None
                page_number = page_match.group(1) if page_match else None
                
                file_link = ""
                if acronym and page_number:
                    pdf_links = {
                        "PPMV": "https://cdn.jsdelivr.net/gh/Sale976/pravilnik/popv.pdf",
                        "PTPV": "https://cdn.jsdelivr.net/gh/Sale976/pravilnik/potp.pdf"
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
