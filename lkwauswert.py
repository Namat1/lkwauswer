import streamlit as st
import pandas as pd
import tempfile
from ftplib import FTP

st.title("LKW-Fahrthäufigkeit je Fahrer")

uploaded_files = st.file_uploader("Excel-Dateien hochladen", type=["xlsx"], accept_multiple_files=True)

# FTP-Upload-Funktion
def upload_via_ftp(local_path, remote_name="2025.csv"):
    try:
        ftp = FTP()
        ftp.connect(st.secrets["ftp"]["host"], 21)
        ftp.login(st.secrets["ftp"]["user"], st.secrets["ftp"]["pass"])
        ftp.cwd("/www/nfc/csv")
        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR " + remote_name, f)
        ftp.quit()
        return True
    except Exception as e:
        st.error(f"FTP-Upload fehlgeschlagen: {e}")
        return False

if uploaded_files:
    eintraege = []

    for file in uploaded_files:
        try:
            df = pd.read_excel(file, sheet_name="Touren", header=None)
            df = df.iloc[4:]  # ab Zeile 5
            df.columns = range(df.shape[1])

            for _, row in df.iterrows():
                lkw = str(row[11]).strip() if 11 in row and pd.notnull(row[11]) else None
                if not lkw or lkw == "0":
                    continue

                # Fahrer-Paar 1: D/E = Spalten 3/4
                if pd.notnull(row[3]) and pd.notnull(row[4]):
                    nname = str(row[3]).strip().title()
                    vname = str(row[4]).strip().title()
                    eintraege.append((nname, vname, lkw))

                # Fahrer-Paar 2: G/H = Spalten 6/7
                if pd.notnull(row[6]) and pd.notnull(row[7]):
                    nname = str(row[6]).strip().title()
                    vname = str(row[7]).strip().title()
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

        # CSV in temporäre Datei schreiben
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False, encoding="utf-8") as tmp:
            df_auswertung.to_csv(tmp.name, index=False, sep=";")
            tmp.flush()

            # FTP-Upload
            if upload_via_ftp(tmp.name, "2025.csv"):
                st.success("✅ CSV-Datei wurde erfolgreich als **2025.csv** per FTP hochgeladen.")
            else:
                st.warning("⚠️ CSV-Datei konnte nicht per FTP hochgeladen werden.")

            # Download-Button anzeigen
            with open(tmp.name, "r", encoding="utf-8") as f:
                st.download_button("⬇️ CSV-Datei herunterladen", f.read(), file_name="2025.csv", mime="text/csv")

        # Tabelle anzeigen
        st.dataframe(df_auswertung)
    else:
        st.warning("Keine gültigen LKW-Fahrten gefunden.")
