import streamlit as st
import pandas as pd
import tempfile
from ftplib import FTP
import os

st.title("LKW-Fahrthäufigkeit je Fahrer")

uploaded_files = st.file_uploader("Excel-Dateien hochladen", type=["xlsx"], accept_multiple_files=True)

# Upload-Funktion mit Fortschrittsbalken
def upload_via_ftp(local_path, remote_name="2025.csv", progress_callback=None):
    try:
        ftp = FTP()
        ftp.connect(st.secrets["FTP_HOST"], 21)
        ftp.login(st.secrets["FTP_USER"], st.secrets["FTP_PASS"])
        ftp.cwd(st.secrets["FTP_BASE_DIR"])

        file_size = os.path.getsize(local_path)
        uploaded = 0

        def callback(data):
            nonlocal uploaded
            uploaded += len(data)
            if progress_callback:
                progress_callback(min(uploaded / file_size, 1.0))

        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR " + remote_name, f, callback=callback)

        ftp.quit()
        return True
    except Exception as e:
        st.error(f"FTP-Upload fehlgeschlagen: {e}")
        return False

if uploaded_files:
    upload_aktiv = st.checkbox("✅ Upload aktivieren")
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

                if pd.notnull(row[3]) and pd.notnull(row[4]):
                    nname = str(row[3]).strip().title()
                    vname = str(row[4]).strip().title()
                    eintraege.append((nname, vname, lkw))

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

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False, encoding="utf-8") as tmp:
            df_auswertung.to_csv(tmp.name, index=False, sep=";")
            tmp.flush()

            progress_bar = st.progress(0)

            if upload_aktiv:
                st.write("🔄 Upload läuft...")
                upload_ok = upload_via_ftp(
                    tmp.name,
                    "2025.csv",
                    progress_callback=lambda p: progress_bar.progress(p)
                )
                if upload_ok:
                    st.success("✅ CSV-Datei wurde erfolgreich als 2025.csv per FTP hochgeladen.")
                else:
                    st.warning("⚠️ Upload fehlgeschlagen.")
            else:
                st.info("☑️ Upload nicht aktiviert. Datei wird nur lokal zum Download angeboten.")

            with open(tmp.name, "r", encoding="utf-8") as f:
                st.download_button("⬇️ CSV-Datei herunterladen", f.read(), file_name="2025.csv", mime="text/csv")
    else:
        st.warning("Keine gültigen LKW-Fahrten gefunden.")
