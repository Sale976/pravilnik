import streamlit as st
import re, os
import streamlit_analytics2 as streamlit_analytics


st.set_page_config(
    page_title="Pretraga PoPV - PoTP",
    layout="wide"
)


# Initialize session state for analytics display
if 'show_analytics' not in st.session_state:
    st.session_state.show_analytics = False

def display_analytics():
    st.session_state.show_analytics = True

st.button("Show Analytics", on_click=display_analytics)

if st.session_state.show_analytics:
    st.header("Analytics Dashboard")
    # Your analytics code here, e.g.,

# --- Title and Description ---
st.markdown(
    """
    <h2 style='text-align: center; font-size:28px;'>
        Web aplikacija za pretragu Pravilnika o Podeli Vozila (PoPV) i Pravilnika o Tehničkom Pregledu (PoTP)
    </h2>
    <p style='font-size:18px; text-align: justify;'>
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
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if st.session_state.search_query.lower() in line.lower():
                        highlighted = re.sub(
                            f"({re.escape(st.session_state.search_query)})",
                            r"<mark>\1</mark>",
                            line.strip(),
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
                            f"📄 Otvori Pravilnik u PDF-u</a>"
                        )

                st.markdown(
                    f"""
                    <div style='display: flex; flex-direction: row; align-items: center;
                                gap: 40px; padding: 5px; background-color: #B9F1C0;
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
