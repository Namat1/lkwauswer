import streamlit as st
import pandas as pd
import io

st.title("LKW-Nutzungsauswertung je Fahrer")

uploaded_files = st.file_uploader("Excel-Dateien hochladen", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    fahrer_lkw = {}

    for file in uploaded_files:
        try:
            df = pd.read_excel(file, sheet_name="Touren", header=None)
            df = df.iloc[4:]
            df.columns = range(df.shape[1])

            for _, row in df.iterrows():
                lkw = str(row[11]).strip() if 11 in row and pd.notnull(row[11]) else None

                # Paar 1: D/E (3/4)
                if 3 in row and pd.notnull(row[3]) and 4 in row and pd.notnull(row[4]):
                    nname = str(row[3]).strip()
                    vname = str(row[4]).strip()
                    key = (nname, vname)
                    if lkw:
                        fahrer_lkw.setdefault(key, set()).add(lkw)

                # Paar 2: G/H (6/7)
                if 6 in row and pd.notnull(row[6]) and 7 in row and pd.notnull(row[7]):
                    nname = str(row[6]).strip()
                    vname = str(row[7]).strip()
                    key = (nname, vname)
                    if lkw:
                        fahrer_lkw.setdefault(key, set()).add(lkw)

        except Exception as e:
            st.error(f"Fehler in Datei {file.name}: {e}")

    if fahrer_lkw:
        daten = []
        for (nachname, vorname), lkw_set in sorted(fahrer_lkw.items()):
            lkw_liste = ", ".join(sorted(lkw_set))
            daten.append([nachname, vorname, lkw_liste])

        df_export = pd.DataFrame(daten, columns=["Nachname", "Vorname", "Gefahrene LKWs"])
        output = io.StringIO()
        df_export.to_csv(output, index=False, sep=";")
        st.download_button("CSV-Datei herunterladen", output.getvalue(), file_name="LKW_je_Fahrer.csv", mime="text/csv")
    else:
        st.warning("Keine gültigen LKW-Einträge gefunden.")
