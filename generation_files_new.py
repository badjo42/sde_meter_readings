from os.path import join
from pathlib import Path
import json
import uuid
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom as minidom

# ---------------------------------------------
# TODO
# -------
#
# Il faut ajouter l'option de mettre le 1er index
# Création de :
#       - Courbe d'index
#       - Index 24h T0, T1, T2
#
# csv (excel):
# 	- nom meter |1er index T0| T1 | T2
#
# Git ?
#
# Nice to have
# ---------------
#
# Generation des fichiers de création
# Generation de prod PV avec la lib PVlib
# Puissance et réactif ?
#
#
#
#
#
#
# ------------------------------------------

# import datetime


# ------------------------------------
# GENERATION DES FICHIERS
# ---------------------------
# Fonction pour générer les noms de meters et metering points
def generate_names(prefix, count):
    return [f"{prefix}_{i}" for i in range(1, count + 1)]


def generate_json_files_from_profiles(
    load_data,
    meter_names,
    readingtype,
    reg_type,
    output_folder="data_generated",
):
    # st.write("start generate_json_files_from_profiles")
    for it, col in enumerate(load_data):
        # Création de la structure de base du dictionnaire JSON
        # st.write("loop start")
        dict_data = {
            "header": {
                "messageId": str(
                    uuid.uuid4()
                ),  # Génération d'un UUID unique pour chaque fichier
                "source": "Amera",
                "verb": "created",
                "noun": "MeterReadings",
                "timestamp": pd.Timestamp.utcnow().strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),  # Timestamp actuel en format UTC
            },
            "payload": {
                "MeterReadings": [
                    {
                        "Meter": {
                            "mRID": meter_names[it],
                            "amrSystem": "Amera",
                        },
                        "IntervalBlocks": [],
                    }
                ]
            },
        }

        # Création de la structure des IntervalBlocks
        tmp_dict = {
            "IntervalReadings": [],
            "ReadingType": {"ref": f"{readingtype[it]}"},
        }

        # st.write("avant remplissage des intervalreadings")
        # Remplissage des IntervalReadings à partir des données de consommation
        for timestamp, value in load_data.iloc[:, it].items():
            tmp_intervalreading = {
                "timeStamp": timestamp.strftime(
                    "%Y-%m-%dT%H:%M:%S%z"
                ),  # Conversion de la date en format ISO 8601
                "value": f"{value}",
                "ReadingQualities": [{"ref": "1.0.0"}],
            }

            tmp_dict["IntervalReadings"].append(tmp_intervalreading)

        # st.write("fin des intervalreadings")
        # Ajout du tmp_dict aux IntervalBlocks du dictionnaire principal
        dict_data["payload"]["MeterReadings"][0]["IntervalBlocks"].append(
            tmp_dict
        )
        # st.write("fin des intervalreadings2")

        # Nom du fichier basé sur le nom du compteur
        json_filename = f"{output_folder}/{col}_{reg_type}.json"

        # st.write("fin des intervalreadings3")

        # Sauvegarde du fichier JSON
        with open(json_filename, "w", encoding="utf-8") as json_file:
            # st.write("creeation du json")
            json.dump(dict_data, json_file, indent=4, ensure_ascii=False)
            # st.write("json cree")

        # print(f"Fichier JSON généré : {json_filename}")
        st.write(f"Fichier JSON généré : {json_filename}")


def timeslice_to_readingtype(x, register_type="A+"):
    return (
        {
            "A+": {
                "15min": "0.0.2.1.1.1.12.0.0.0.0.0.0.0.0.3.72.0",
                "T0": "0.0.4.1.1.1.12.0.0.0.0.0.0.0.0.3.72.0",
                "T1": "0.0.4.1.1.1.12.0.0.0.0.1.0.0.0.3.72.0",
                "T2": "0.0.4.1.1.1.12.0.0.0.0.2.0.0.0.3.72.0",
            },
            "A-": {
                "15min": "0.0.2.1.19.1.12.0.0.0.0.0.0.0.0.3.72.0",
                "T0": "0.0.4.1.19.1.12.0.0.0.0.0.0.0.0.3.72.0",
                "T1": "0.0.4.1.19.1.12.0.0.0.0.1.0.0.0.3.72.0",
                "T2": "0.0.4.1.19.1.12.0.0.0.0.2.0.0.0.3.72.0",
            },
        }
        .get(register_type)
        .get(x)
    )


# Fonction fictive pour générer les fichiers (à personnaliser)
def generate_file(load_curves, register_type=["A+"]):
    for reg in register_type:
        st.write(
            f"Generating {reg} file from {load_curves.index[0]} to {load_curves.index[-1]}"
        )

        # load_curves

        meter_names = load_curves.columns.tolist()
        # meter_names = index_curves_24h.columns.tolist()
        st.write(f"Meter names: {meter_names}")

        tmp_names = []
        tmp_readingtype = []
        for elem in meter_names:
            tmp_names.append("_".join(elem.split("_")[:-1]))
            tmp_readingtype.append(
                timeslice_to_readingtype(elem.split("_")[-1], register_type=reg)
            )

        # st.write(f"Metering point names: {metering_point_names}")
        # st.write(tmp_names)
        # st.write(tmp_readingtype)

        # generate_json_files_from_profiles(index_curves_24h, tmp_names, tmp_readingtype)
        # st.write("start generate json")
        generate_json_files_from_profiles(
            load_curves, tmp_names, tmp_readingtype, reg
        )

        st.success("file successfully generated!")


# --------------------------------------
# GENERATION COURBES DE CHARGE ET INDEX
# -----------------------------------
# Fonction pour générer un profil de charge journalier typique
def generate_daily_profile(points_per_day=96):
    # Calculer le facteur d'échelle pour chaque période en fonction du nombre de points par jour
    hours_per_point = 24 / points_per_day
    profile = np.zeros(points_per_day)

    for i in range(points_per_day):
        # Conversion de l'index en heure de la journée
        hour_of_day = i * hours_per_point

        maximum = 10.0
        # Générer le profil en fonction de l'heure de la journée
        if (11 <= hour_of_day < 13) or (
            18 <= hour_of_day < 21
        ):  # Midi, soupé - pic de consommation
            profile[i] = maximum
        elif 13 <= hour_of_day < 18:  # Journée - charge modérée
            profile[i] = 0.7 * maximum
        else:  # Nuit - basse consommation
            profile[i] = 0.2 * maximum

    return profile


# Fonction pour ajouter du bruit autour du profil
def add_noise(profile, noise_level=0.1):
    noisy_profile = profile + np.random.normal(0, noise_level, len(profile))
    return np.clip(noisy_profile, 0, None)  # Pour éviter des valeurs négatives


# Fonction pour générer une courbe de charge électrique pour plusieurs jours
def generate_electric_load_curve(
    start_date, end_date, meter_names, points_per_day=96, noise_level=0.1
):
    # Générer la plage de dates en fonction du nombre de points par jour
    freq = f"{1440 // points_per_day}min"  # Intervalle en minutes par point (1440 minutes dans une journée)
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    # Initialiser un DataFrame pour stocker les données des courbes de charge
    load_data = pd.DataFrame(index=date_range)

    # Générer un profil journalier de base pour la résolution demandée
    daily_profile = generate_daily_profile(points_per_day)

    for meter in meter_names:
        # Répéter le profil journalier pour couvrir toute la plage de dates
        num_days = len(load_data) // points_per_day

        # Ajustement : S'assurer que la longueur du profil répété correspond à la longueur de l'index
        daily_profile_repeated = np.tile(
            daily_profile, num_days + 1
        )  # Répéter une fois de plus pour couvrir toute la période
        noisy_daily_profile = add_noise(
            daily_profile_repeated[: len(load_data)], noise_level
        )  # Troncature pour correspondre à la longueur

        load_data[meter] = noisy_daily_profile[: len(load_data)]

    return load_data

reading_type_labels = {
    'ACTIVE_DELIVERY_READ15T': '0.0.2.1.1.1.12.0.0.0.0.0.0.0.0.0.72.0',
    'ACTIVE_DELIVERY_READ24H': '0.0.4.1.1.1.12.0.0.0.0.0.0.0.0.0.72.0',
    'ACTIVE_DELIVERY_READ24H_T1': '0.0.4.1.1.1.12.0.0.0.0.1.0.0.0.0.72.0',
    'ACTIVE_DELIVERY_READ24H_T2': '0.0.4.1.1.1.12.0.0.0.0.2.0.0.0.0.72.0',
    'ACTIVE_REDELIVERY_READ15T': '0.0.2.1.19.1.12.0.0.0.0.0.0.0.0.0.72.0',
    'ACTIVE_REDELIVERY_READ24H': '0.0.4.1.19.1.12.0.0.0.0.0.0.0.0.0.72.0',
    'ACTIVE_REDELIVERY_READ24H_T1': '0.0.4.1.19.1.12.0.0.0.0.1.0.0.0.0.72.0',
    'ACTIVE_REDELIVERY_READ24H_T2': '0.0.4.1.19.1.12.0.0.0.0.2.0.0.0.0.72.0',
    'REACTIVE_INDUCTIVE_DELIVERY_READ15T': '0.0.2.1.15.1.12.0.0.0.0.0.0.0.0.0.73.0',
    'REACTIVE_INDUCTIVE_DELIVERY_READ24H': '0.0.4.1.15.1.12.0.0.0.0.0.0.0.0.0.73.0',
    'REACTIVE_INDUCTIVE_DELIVERY_READ24H_T1': '0.0.4.1.15.1.12.0.0.0.0.1.0.0.0.0.73.0',
    'REACTIVE_INDUCTIVE_DELIVERY_READ24H_T2': '0.0.4.1.15.1.12.0.0.0.0.2.0.0.0.0.73.0',
    'REACTIVE_INDUCTIVE_REDELIVERY_READ15T': '0.0.2.1.17.1.12.0.0.0.0.0.0.0.0.0.73.0',
    'REACTIVE_INDUCTIVE_REDELIVERY_READ24H': '0.0.4.1.17.1.12.0.0.0.0.0.0.0.0.0.73.0',
    'REACTIVE_INDUCTIVE_REDELIVERY_READ24H_T1': '0.0.4.1.17.1.12.0.0.0.0.1.0.0.0.0.73.0',
    'REACTIVE_INDUCTIVE_REDELIVERY_READ24H_T2': '0.0.4.1.17.1.12.0.0.0.0.2.0.0.0.0.73.0',
    'REACTIVE_CAPACITIVE_DELIVERY_READ15T': '0.0.2.1.16.1.12.0.0.0.0.0.0.0.0.0.73.0',
    'REACTIVE_CAPACITIVE_DELIVERY_READ24H': '0.0.4.1.16.1.12.0.0.0.0.0.0.0.0.0.73.0',
    'REACTIVE_CAPACITIVE_DELIVERY_READ24H_T1': '0.0.4.1.16.1.12.0.0.0.0.1.0.0.0.0.73.0',
    'REACTIVE_CAPACITIVE_DELIVERY_READ24H_T2': '0.0.4.1.16.1.12.0.0.0.0.2.0.0.0.0.73.0',
    'REACTIVE_CAPACITIVE_REDELIVERY_READ15T': '0.0.2.1.18.1.12.0.0.0.0.0.0.0.0.0.73.0',
    'REACTIVE_CAPACITIVE_REDELIVERY_READ24H': '0.0.4.1.18.1.12.0.0.0.0.0.0.0.0.0.73.0',
    'REACTIVE_CAPACITIVE_REDELIVERY_READ24H_T1': '0.0.4.1.18.1.12.0.0.0.0.1.0.0.0.0.73.0',
    'REACTIVE_CAPACITIVE_REDELIVERY_READ24H_T2': '0.0.4.1.18.1.12.0.0.0.0.2.0.0.0.0.73.0',
}

# CHECK FOLDER
# ---------------
dossiers = [
    join(".", "data_generated"),
]

for dossier in dossiers:
    dossier_path = Path(dossier)
    if not dossier_path.exists():
        dossier_path.mkdir(parents=False)
        print(f"Le dossier {dossier} a été créé.")
    else:
        pass


# STREAMLIT DASHBOARD
# -------------------
# --- STREAMLIT MAIN PAGE ---

st.set_page_config(layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisissez une fonctionnalité",
    ["Génération MeterReadings", "Création Meter & Metering Point"],
)

# ------------------------------------------------------------------
#
#
#
#   METER READINGS
#
#
#
# --------------------------------------------------------------------
if page == "Génération MeterReadings":
    # Configuration du tableau de bord
    st.title("Dashboard de génération de fichiers")

    # Choix de la courbe à générer
    curve_type = st.selectbox(
        "Choisissez le type de courbe à générer",
        ["Index 15min", "Index 24h T0", "Index 24h T1/T2", "Tout"],
    )

    # Choix du type de registre (A+ et ou A-)
    register_types = st.multiselect(
        "Choississez le type de registre à générer (A+ et/ou A-)",
        ["A+", "A-"],
        ["A+"],
    )
    # Option pour entrer manuellement ou via un fichier
    input_type = st.radio(
        "Choisissez comment fournir les paramètres des meters",
        (
            "Manuellement",
            "Via un fichier XLSX",
            # "Générer automatiquement X meters via un préfix",
        ),
    )

    # Variables pour stocker les noms des meters et metering points
    meter_names = []

    if input_type == "Manuellement":
        # Entrer les noms manuellement
        if curve_type == "Index 15min":
            lines = st.text_area(
                "Entrez les noms des meters, 1er index [kWh] (un par ligne)"
            ).split("\n")
            # st.write(lines)

            meter_names = []
            first_indext0 = []
            for elem in lines:
                parts = elem.strip().split(",")
                if len(parts) >= 2:
                   try:
                       meter_names.append(parts[0].strip())
                       first_indext0.append(float(parts[1].strip()))
                   except ValueError:
                       st.warning(f"⚠️ Ligne ignorée (valeur invalide) : {elem}")
                elif elem.strip() != "":
                   st.warning(f"⚠️ Ligne ignorée (format incorrect) : {elem}")
        elif curve_type == "Index 24h T0":
            lines = st.text_area(
                "Entrez les noms des meters, 1er index [kWh] (un par ligne)"
            ).split("\n")

            meter_names = []
            first_indext0 = []
            for elem in lines:
                parts = elem.strip().split(",")
                if len(parts) >= 2:
                    try:
                        meter_names.append(parts[0].strip())
                        first_indext0.append(float(parts[1].strip()))
                    except ValueError:
                        st.warning(f"⚠️ Ligne ignorée (valeur invalide) : {elem}")
                elif elem.strip() != "":
                    st.warning(f"⚠️ Ligne ignorée (format incorrect) : {elem}")
        elif curve_type == "Index 24h T1/T2":
            # st.write("on entre dans index24h t1/t2")
            lines = st.text_area(
                "Entrez les noms des meters, 1er index T1 [kWh], 1er index T2 [kWh] (un par ligne)"
            ).split("\n")

            # st.write(lines)
            # st.write("ok lines")

            meter_names = []
            first_indext1 = []
            first_indext2 = []
            for elem in lines:
                parts = elem.strip().split(",")
                if len(parts) >= 3:
                    try:
                        meter_names.append(parts[0].strip())
                        first_indext1.append(float(parts[1].strip()))
                        first_indext2.append(float(parts[2].strip()))
                    except ValueError:
                        st.warning(f"⚠️ Ligne ignorée (valeur invalide) : {elem}")
                elif elem.strip() != "":
                    st.warning(f"⚠️ Ligne ignorée (format incorrect) : {elem}")
        elif curve_type == "Tout":
            lines = st.text_area(
                "Entrez les noms des meters, 1er index T0 [kWh], 1er index T1 [kWh], 1er index T2 [kWh] (un par ligne)"
            ).split("\n")

            meter_names = []
            first_indext0 = []
            first_indext1 = []
            first_indext2 = []
            for elem in lines:
                parts = elem.strip().split(",")
                if len(parts) >= 4:
                    try:
                        meter_names.append(parts[0].strip())
                        first_indext0.append(float(parts[1].strip()))
                        first_indext1.append(float(parts[2].strip()))
                        first_indext2.append(float(parts[3].strip()))
                    except ValueError:
                        st.warning(f"⚠️ Ligne ignorée (valeur invalide) : {elem}")
                elif elem.strip() != "":
                    st.warning(f"⚠️ Ligne ignorée (format incorrect) : {elem}")
        else:
            raise SystemExit("Le type de courbe n'est pas correcte")

    elif input_type == "Via un fichier XLSX":
        # Importer les noms depuis un fichier CSV
        uploaded_file = st.file_uploader(
            "Téléchargez un fichier CSV contenant 4 colonnes : meter, 1er index T0 [kWh], 1er index T1 [kWh], 1er index T2 [kWh]. Les index non nécessaires pour la génération seront ignorés"
        )
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)
            meter_names = df["Nom du meter"].tolist()
            if curve_type == "Index 15min":
                first_indext0 = [0] * len(meter_names)
            elif curve_type == "Index 24h T0":
                first_indext0 = df["1er index T0"].tolist()
            elif curve_type == "Index 24h T1/T2":
                first_indext1 = df["1er index T1"].tolist()
                first_indext2 = df["1er index T2"].tolist()
            elif curve_type == "Tout":
                first_indext0 = df["1er index T0"].tolist()
                first_indext1 = df["1er index T1"].tolist()
                first_indext2 = df["1er index T2"].tolist()
            else:
                raise SystemExit("Le type de courbe n'est pas correcte")

            st.write("Aperçu du fichier importé :")
            st.dataframe(df)

    # elif input_type == "Générer automatiquement X meters via un préfix":
    #     # Générer des noms automatiquement avec un préfixe
    #     meter_prefix = st.text_input("Préfixe pour les meters")
    #     count = st.number_input(
    #         "Nombre de meters à générer", min_value=1, value=5
    #     )

    #     meter_names = generate_names(meter_prefix, count)

    #     st.write("Meters générés :", meter_names)

    # Choix du range de dates
    start_date = st.date_input(
        "Date de début", pd.Timestamp.today() - pd.Timedelta(days=7)
    )
    start_date = pd.to_datetime(start_date).tz_localize(
        "Europe/Zurich"
    )  # timestamp zurich

    end_date = st.date_input("Date de fin", pd.Timestamp.today())
    end_date = pd.to_datetime(end_date).tz_localize(
        "Europe/Zurich"
    )  # timestamp zurich

    date_range = (start_date, end_date)

    afficher_plot = st.checkbox("Afficher le graphique ?")
    # Bouton pour lancer la génération des fichiers
    if st.button("Générer"):
        # generate_file(meter_names, metering_point_names, curve_type, date_range)

        # Générer les courbes de charge
        # print("test")
        # st.write("Debut")
        load_curves = generate_electric_load_curve(
            start_date,
            end_date,
            meter_names,
            points_per_day=96,
            noise_level=1.5,
        )
        # st.write("Apres generate_electric_load_curve")
        if curve_type == "Index 15min":
            # st.write("Index 15min")
            index_curves = load_curves.cumsum() + first_indext0
            index_curves = index_curves.add_suffix("_15min")
        elif curve_type == "Index 24h T0":
            # st.write("Index 24h T0")
            index_curves = load_curves.cumsum() + first_indext0
            index_curves = index_curves.asfreq("1D", method="pad")
            index_curves = index_curves.add_suffix("_T0")
        elif curve_type == "Index 24h T1/T2":
            # st.write("Index 24h T1/T2")
            index_curves = load_curves.cumsum()
            index_curves = index_curves.asfreq("1D", method="pad")
            index_curves = pd.concat(
                [
                    index_curves.add_suffix("_T1") + first_indext1,
                    index_curves.add_suffix("_T2") + first_indext2,
                ],
                axis=1,
            )
        elif curve_type == "Tout":
            # st.write("Tout")
            index_curves_15min = load_curves.cumsum() + first_indext0
            index_curves_15min = index_curves_15min.add_suffix("_15min")

            index_curves_24h = load_curves.cumsum()
            index_curves_24h = index_curves_24h.asfreq("1D", method="pad")
            index_curves_24h = pd.concat(
                [
                    index_curves_24h.add_suffix("_T0") + first_indext0,
                    index_curves_24h.add_suffix("_T1") + first_indext2,
                    index_curves_24h.add_suffix("_T2") + first_indext2,
                ],
                axis=1,
            )
        else:
            raise SystemExit("Le type de courbe n'est pas correcte")
        # index_curves = load_curves.cumsum() + first_indext0

        if curve_type == "Tout":
            # st.write("Generate tout")
            generate_file(index_curves_15min, register_types)
            generate_file(index_curves_24h, register_types)
        else:
            # st.write("Generate else")
            # st.dataframe(index_curves)
            generate_file(index_curves, register_types)

        if afficher_plot:
            # st.write("Afficher plot")
            # Afficher les courbes
            fig = plt.figure(figsize=(10, 6))
            fig.clf()
            ax = fig.gca()

            if curve_type == "Tout":
                for column in index_curves_15min.columns:
                    plt.plot(
                        index_curves_15min.index,
                        index_curves_15min[column],
                        ".-",
                        label=column,
                    )
                for column in index_curves_24h.columns:
                    plt.plot(
                        index_curves_24h.index,
                        index_curves_24h[column],
                        ".-",
                        label=column,
                    )
            else:
                for column in index_curves.columns:
                    plt.plot(
                        index_curves.index,
                        index_curves[column],
                        ".-",
                        label=column,
                    )

            ax.set_xlabel("Date")
            ax.set_ylabel("Charge (kW)")
            ax.legend()
            ax.grid(True)
            # plt.xticks(rotation=45)
            fig.autofmt_xdate()
            fig.tight_layout()

            st.pyplot(fig)

# ---------------------------------------------------------------------------
#
#
#
#
#
#   XML CONFIGURATION M/MP
#
#
#
#
# --------------------------------------------------------------------
elif page == "Création Meter & Metering Point":
    st.title("Création des Meters & Metering Points")
    st.write(
        "Cette section permettra de générer les fichiers JSON nécessaires à la création des compteurs et points de comptage. Ces fichiers doivent être importées directement dans EnergyWorx. Les tabs sont dépendantes les unes des autres, commencez dans l'ordre"
    )
    
        
        
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["A - Meter Config", "B - Usage Point Config", "C - Customer Agreement Config", "D - Master Data Linkage"])
    
    # -------------------- Tab 1 - MeterConfig --------------------
    with tab1:
        st.header("A - MeterConfig")
        st.session_state["meter_id"] = st.text_input("Nom et ID du compteur (mRID)", value="ESR1030612001234")
        st.session_state["serial"] = st.text_input("Numéro de série", value="1234567")
        st.session_state["model"] = st.text_input("Modèle", value="E-eRS801-STO-50")
        st.session_state["installation_date"] = st.date_input("Date d'installation", value=pd.Timestamp.today())
        st.session_state["multiplier"] = st.number_input("Multiplicateur du compteur", value=1)
    
        st.session_state["selected_readings"] = st.multiselect(
            "Sélectionnez les types de lecture :",
            options=reading_type_labels.keys(),
            default=[
                'ACTIVE_DELIVERY_READ15T',
                'ACTIVE_DELIVERY_READ24H',
                'ACTIVE_REDELIVERY_READ15T',
                'ACTIVE_REDELIVERY_READ24H',
            ],
            key="multiselect_readings"
        )
        
        if st.button("📦 Générer le fichier Meter Config"):
            # channels = [{"isVirtual": False, "ReadingType": {"ref": reading_type_labels[label]}} for label in st.session_state["selected_readings"]]
            channels = [{
                "mRID": "0000",
                "leftDigitCount": 8,
                "rightDigitCount": 0,
                "Channels": [
                    {
                        "isVirtual": False,
                        "ReadingType": {
                            "ref": reading_type_labels[label]
                        }
                    }
                ]
            } for label in st.session_state["selected_readings"]
            ]
            meter_config = {
                "header": {
                        "messageId": str(uuid.uuid4()),
                        "correlationId": str(uuid.uuid4()),
                        "timestamp": pd.Timestamp.utcnow().tz_localize(None).isoformat() + "Z",
                        "source": "Innosolv",
                        "ackRequired": True,
                        "verb": "created",
                        "noun": "MeterConfig"
                    },
                "payload": {
                    "MeterConfig": {
                        "mRID": st.session_state["meter_id"],
                        "serialNumber": st.session_state["serial"],
                        "assetID": st.session_state["serial"],
                        "timeZoneOffset": "Europe/Zurich",
                        "MetrologyFunction": {"Registers": channels},
                        "EndDeviceInfo": {"AssetModel": {"modelNumber": st.session_state["model"]}},
                        "Lifecycle": {"installationDate": st.session_state["installation_date"].isoformat() + "T00:00:00.000Z"},
                        "MeterMultipliers": [{"kind": "multiplierFactor", "value": st.session_state["multiplier"]}],
                    }
                }
            }
            st.download_button("📥 Télécharger MeterConfig", json.dumps(meter_config, indent=4, ensure_ascii=False), file_name=f"A-meter-config-{st.session_state['meter_id']}.json")
    
    # -------------------- Tab 2 - Usage Point --------------------
    with tab2:
        st.header("B - UsagePointConfig")
        st.session_state["usage_point_id"] = st.text_input("Metering Point mRID", value="CH0000080023200000000000000005938")
        st.session_state["postal_code"] = st.text_input("Code postal", value="1630")
        st.session_state["town"] = st.text_input("Ville", value="Bulle")
        st.session_state["canton"] = st.text_input("Canton", value="FR")
        st.session_state["company_name"] = st.text_input("Nom de la société", value="Gruyère Energie SA")
        st.session_state["install_date"] = st.date_input("Date de création", value=pd.Timestamp.today())
        
        if st.button("📦 Générer le fichier Usage Point Config"):
            usage_point_config = {
                "header": {
                        "messageId": str(uuid.uuid4()),
                        "correlationId": str(uuid.uuid4()),
                        "timestamp": pd.Timestamp.utcnow().tz_localize(None).isoformat() + "Z",
                        "source": "Innosolv",
                        "ackRequired": True,
                        "verb": "created",
                        "noun": "UsagePointConfig"
                    },
                "payload": {
                    "UsagePointConfig": {
                        "mRID": st.session_state["usage_point_id"],
                        "isVirtual": False,
                        "UsagePointLocation": {
                            "mRID": "123456",
                            "mainAddress": {
                                "streetDetail": {"name": "Rue de la soif", "number": "42"},
                                "townDetail": {"code": st.session_state["postal_code"], "name": st.session_state["town"], "country": "Suisse", "stateOrProvince": st.session_state["canton"]},
                            },
                        },
                        "GridOwner": {"mRID": "12X-0000001471-5", "name": st.session_state["company_name"], "createdDateTime": st.session_state["install_date"].isoformat() + "T00:00:00.000Z"},
                        "EnergyServiceSupplier": {"mRID": "12X-0000000639-U", "name": st.session_state["company_name"], "createdDateTime": st.session_state["install_date"].isoformat() + "T00:00:00.000Z"},
                        "BalanceGroup": {"mRID": "12XFMV-WEG-----N", "name": "FMV", "createdDateTime": st.session_state["install_date"].isoformat() + "T00:00:00.000Z"},
                    }
                }
            }
            st.download_button("📥 Télécharger UsagePointConfig", json.dumps(usage_point_config, indent=4, ensure_ascii=False), file_name=f"B-usage-point-config-{st.session_state['usage_point_id']}.json")
    
    # -------------------- Tab 3 - Customer Agreement --------------------
    with tab3:
        st.header("C - CustomerAgreementConfig")
        st.session_state["tarif_name"] = st.text_input("Nom du tarif", value="A-Double")
        st.session_state["start_date"] = st.date_input("Date de début du contrat", value=pd.Timestamp.today())
        
        if st.button("📦 Générer le fichier Customer Agreement Config"):
            customer_agreement_config = {
                "header": {
                        "messageId": str(uuid.uuid4()),
                        "correlationId": str(uuid.uuid4()),
                        "timestamp": pd.Timestamp.utcnow().tz_localize(None).isoformat() + "Z",
                        "source": "Innosolv",
                        "ackRequired": True,
                        "verb": "created",
                        "noun": "CustomerAgreementConfig"
                    },
                "payload": {
                    "CustomerAgreementConfig": {
                        "mRID": "123456",
                        "UsagePoint": {"mRID": st.session_state["usage_point_id"]},
                        "type": "Acheminement",
                        "PricingStructures": {"Tariffs": [{"mRID": "1234", "name": st.session_state["tarif_name"]}]},
                        "validityInterval": {"start": st.session_state["start_date"].isoformat() + "T00:00:00.000Z"},
                    }
                }
            }
            st.download_button("📥 Télécharger CustomerAgreementConfig", json.dumps(customer_agreement_config, indent=4, ensure_ascii=False), file_name=f"C-customer-agreement-{st.session_state['usage_point_id']}.json")
        
    # -------------------- Tab 4 - Master Data Linkage + Génération --------------------
    with tab4:
        st.header("D - MasterDataLinkageConfig")
        st.session_state["config_date"] = st.date_input("Date de configuration", value=pd.Timestamp.today())


        if st.button("📦 Générer le fichier Master Data Linkage"):
            channels_2 = [{"ReadingType": {"ref": reading_type_labels[label]}} for label in st.session_state["selected_readings"]]
            master_data_config = {
                "header": {
                        "messageId": str(uuid.uuid4()),
                        "correlationId": str(uuid.uuid4()),
                        "timestamp": pd.Timestamp.utcnow().tz_localize(None).isoformat() + "Z",
                        "source": "Innosolv",
                        "ackRequired": True,
                        "verb": "created",
                        "noun": "MasterDataLinkageConfig"
                    },
                "payload": {
                    "MasterDataLinkageConfig": {
                        "ConfigurationEvent": {"createdDateTime": st.session_state["config_date"].isoformat() + "T00:00:00.000Z", "reason": "MeterInstallation"},
                        "Meter": {"mRID": st.session_state["meter_id"]},
                        "MasterData": [
                            {"mRID": st.session_state["meter_id"], "masterDataType": "Meter", "relatedMasterData": {"mRID": st.session_state["usage_point_id"]}, "Channels": channels_2},
                            {"mRID": st.session_state["usage_point_id"], "masterDataType": "UsagePoint", "relatedMasterData": {"mRID": st.session_state["meter_id"], "assetID": st.session_state["serial"]}, "Channels": channels_2},
                        ]
                    }
                }
            }
            st.download_button("📥 Télécharger MasterDataLinkageConfig", json.dumps(master_data_config, indent=4, ensure_ascii=False), file_name=f"D-master-data-linkage-{st.session_state['meter_id']}-{st.session_state['usage_point_id']}.json")