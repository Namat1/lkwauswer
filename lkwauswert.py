import streamlit as st
import pandas as pd
import io

st.title("LKW-Fahrthäufigkeit je Fahrer")

uploaded_files = st.file_uploader("Excel-Dateien hochladen", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    eintraege = []

    for file in uploaded_files:
        try:
            df = pd.read_excel(file, sheet_name="Touren", header=None)
            df = df.iloc[4:]
            df.columns = range(df.shape[1])

            for _, row in df.iterrows():
                lkw = str(row[11]).strip() if 11 in row and pd.notnull(row[11]) else None
                if not lkw or lkw == "0":
                    continue

                # Paar D/E (3/4)
                if pd.notnull(row[3]) and pd.notnull(row[4]):
                    nname = str(row[3]).strip()
                    vname = str(row[4]).strip()
                    eintraege.append((nname, vname, lkw))

                # Paar G/H (6/7)
                if pd.notnull(row[6]) and pd.notnull(row[7]):
                    nname = str(row[6]).strip()
                    vname = str(row[7]).strip()
                    eintraege.append((nname, vname, lkw))

        except Exception as e:
            st.error(f"Fehler in Datei {file.name}: {e}")

    if eintraege:
        df_lkw = pd.DataFrame(eintraege, columns=["Nachname", "Vorname", "LKW"])
        df_auswertung = (
            df_lkw.groupby(["Nachname", "Vorname", "LKW"])
            .size()
            .reset_index(name="Anzahl Fahrten")
            .sort_values(by=["Nachname", "Vorname", "Anzahl Fahrten"], ascending=[True, True, False])
        )

        output = io.StringIO()
        df_auswertung.to_csv(output, index=False, sep=";")
        st.download_button("CSV-Datei herunterladen", output.getvalue(), file_name="LKW_Haeufigkeit_je_Fahrer.csv", mime="text/csv")

        st.dataframe(df_auswertung)
    else:
        st.warning("Keine gültigen LKW-Fahrten gefunden.")
