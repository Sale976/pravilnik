import streamlit as st
import re

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
        f.write("Član 12 se odnosi na tehnički pregled vozila. Strana 15.\n")
        f.write("PoTP reguliše tehničke uslove. Strana 22.\n")
        f.write("Ovaj red ne sadrži ništa relevantno.\n")
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
                st.markdown(
                    f"<div style='padding: 10px; background-color: #f4f4f4; "
                    f"border-left: 4px solid #0077b6; margin-bottom: 10px; font-size:17px;'>"
                    f"{match}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Nisu pronađeni odgovarajući rezultati!")
    else:
        st.info("")  # Empty space when no search

    st.markdown("</div>", unsafe_allow_html=True)
