import streamlit as st
import re
import time

st.set_page_config(
    page_title="Pretraga PoPV - PoTP",
    layout="wide"
)

# --- Custom Styled Title and Info Text ---
st.markdown(
    """
    <h2 style='text-align: center; margin-top: 0; font-size:28px;'>
        Web aplikacija za pretragu Pravilnika o Podeli (PoPV) i Pravilnika o Tehničkom Pregledu (PoTP)
    </h2>
    <p style='font-size:18px; text-align: justify;'>
        🛈 Aplikacija ne vrši pretragu Pravilnika (PoPV, PoTP) nego poseban tekstualni fajl koji vam pri pretrazi prikazuje broj Člana i na kojoj stranici se nalazi!
    </p>
    <p style='font-size:18px; text-align: justify;'>
        🛈 Broj strane prikazan u rezultatu pretrage važi isključivo ako su pravilnici preuzeti sa Pravno Informacionog Sistema bez bilo kakvih izmena pri štampanju!
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

file_path = "pravilnik.txt"

# --- Create file if needed ---
try:
    with open(file_path, "x", encoding="utf-8") as f:
        f.write("Član 12 se odnosi na tehnički pregled vozila. (PoTP) Str. 15.\n")
        f.write("PoTP reguliše tehničke uslove. Str. 22.\n")
        f.write("ABS (kočenje) -- Član 30 (PoPV) str. 35\n")
except FileExistsError:
    pass

# --- Layout: Two columns ---
col1, col2 = st.columns([1, 2])

# --- Left Column: Search Input & Button ---
with col1:
    search_query = st.text_input(
        r"$\textsf{\large Unesite tekst za pretragu:}$",
        value=st.session_state.search_query,
        key="search_query"
    )
    st.button("Obrišite rezultate pretrage", on_click=clear_search)

# --- Right Column: Display Results ---
with col2:
    st.markdown("<div style='margin-top: 32px;'>", unsafe_allow_html=True)

    matching_lines = []

    if st.session_state.search_query:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if st.session_state.search_query.lower() in line.lower():
                        # Highlight matching text
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
                "<h3 style='color: #0077b6; font-size: 24px;'>🔍 Rezultati pretrage:</h3>",
                unsafe_allow_html=True
            )

            for match in matching_lines:
                # Extract acronym and page number
                acronym_match = re.search(r"\((PoPV|PoTP)\)", match)
                page_match = re.search(r"[Ss]tr\.*\s*(\d+)", match)

                acronym = acronym_match.group(1) if acronym_match else None
                page_number = page_match.group(1) if page_match else None

                file_link = ""
                if acronym and page_number:
                    drive_file_id = "1wkVMLXFWPY8dAkam7KRbJwNkq7kBBcuy"
                    pdf_url = f"https://drive.google.com/file/d/{drive_file_id}/preview#page={page_number}"
                    file_link = (
                        f"<a href='{pdf_url}' target='_blank' "
                        f"title='Kliknite da otvorite PDF na odgovarajućoj stranici' "
                        f"style='color:#0077b6; font-weight: bold; text-decoration: none;'>"
                        f"📄 Otvori PDF</a>"
                    )

                # Display result and link side by side with ~1cm spacing
                st.markdown(
                    f"""
                    <div style='display: flex; flex-direction: row; align-items: center; gap: 40px;
                                padding: 10px; background-color: #f4f4f4;
                                border-left: 4px solid #0077b6; margin-bottom: 10px;
                                font-size:17px; flex-wrap: wrap;'>
                        <div>{match}</div>
                        <div>{file_link}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Nisu pronađeni odgovarajući rezultati!")
    else:
        st.info("")  # Placeholder spacing

    st.markdown("</div>", unsafe_allow_html=True)
