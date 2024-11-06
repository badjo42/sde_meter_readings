from os.path import join
from pathlib import Path
import json
import uuid
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
    load_data, meter_names, readingtype,reg_type, output_folder="data_generated"
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
                        "Meter": {"mRID": meter_names[it], "amrSystem": "Amera"},
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
        for timestamp, value in load_data.iloc[:,it].items():
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

def timeslice_to_readingtype(x,register_type='A+'):
    return {'A+':
                {
                "15min" : "0.0.2.1.1.1.12.0.0.0.0.0.0.0.0.3.72.0",
                "T0" : "0.0.4.1.1.1.12.0.0.0.0.0.0.0.0.3.72.0",
                "T1" : "0.0.4.1.1.1.12.0.0.0.0.1.0.0.0.3.72.0",
                "T2" : "0.0.4.1.1.1.12.0.0.0.0.2.0.0.0.3.72.0",
                },
            'A-':
                {
                "15min" : "0.0.2.1.19.1.12.0.0.0.0.0.0.0.0.3.72.0",
                "T0" : "0.0.4.1.19.1.12.0.0.0.0.0.0.0.0.3.72.0",
                "T1" : "0.0.4.1.19.1.12.0.0.0.0.1.0.0.0.3.72.0",
                "T2" : "0.0.4.1.19.1.12.0.0.0.0.2.0.0.0.3.72.0",
                }
        }.get(register_type).get(x)

# Fonction fictive pour générer les fichiers (à personnaliser)
def generate_file(load_curves,register_type=['A+']):
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
            tmp_names.append(elem.split("_")[0])
            tmp_readingtype.append(timeslice_to_readingtype(elem.split("_")[1],register_type=reg))
            
        # st.write(f"Metering point names: {metering_point_names}")
        # st.write(tmp_names)
        # st.write(tmp_readingtype)

        # generate_json_files_from_profiles(index_curves_24h, tmp_names, tmp_readingtype)
        # st.write("start generate json")
        generate_json_files_from_profiles(load_curves, tmp_names, tmp_readingtype,reg)

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













# curve_type = "Index 15min"
# lines = "test3,1\ntest4,10"

# # curve_type = "Index 24h T0"
# # lines = "test3,1\ntest4,10"

# # curve_type = "Index 24h T1/T2"
# # lines = "test3,1,3\ntest4,10,5"

# # curve_type = "Tout"
# # lines = "test3,1,3,4\ntest4,10,5,8"


# # # Option pour entrer manuellement ou via un fichier
# # input_type = st.radio(
# #     "Choisissez comment fournir les paramètres des meters",
# #     (
# #         "Manuellement",
# #         "Via un fichier XLSX",
# #         # "Générer automatiquement X meters via un préfix",
# #     ),
# # )

# # Variables pour stocker les noms des meters et metering points
# meter_names = []

# # lines = "test3,1\ntest4,10"
# # lines = "test3,1\ntest4,10"

# if curve_type == "Index 15min":
#     meter_names = []
#     first_indext0 = []
#     for elem in lines.split("\n"):
#         meter_names.append(elem.split(',')[0])
#         first_indext0.append(float(elem.split(',')[1]))
# elif curve_type == "Index 24h T0":
#     meter_names = []
#     first_indext0 = []
#     for elem in lines.split("\n"):
#         meter_names.append(elem.split(',')[0])
#         first_indext0.append(float(elem.split(',')[1]))
# elif curve_type == "Index 24h T1/T2":
#     meter_names = []
#     first_indext1 = []
#     first_indext2 = []
#     for elem in lines.split("\n"):
#         meter_names.append(elem.split(',')[0])
#         first_indext1.append(float(elem.split(',')[1]))
#         first_indext2.append(float(elem.split(',')[2]))
# elif curve_type == "Tout":
#     meter_names = []
#     first_indext0 = []
#     first_indext1 = []
#     first_indext2 = []
#     for elem in lines.split("\n"):
#         meter_names.append(elem.split(',')[0])
#         first_indext0.append(float(elem.split(',')[1]))
#         first_indext1.append(float(elem.split(',')[2]))
#         first_indext2.append(float(elem.split(',')[3]))
# else:
#     raise SystemExit("Le type de courbe n'est pas correcte")

# # elif input_type == "Via un fichier XLSX":
# #     # Importer les noms depuis un fichier CSV
# #     uploaded_file = st.file_uploader(
# #         "Téléchargez un fichier CSV contenant 4 colonnes : meter, 1er index T0, 1er index T1, 1er index T2. Les index non nécessaires pour la génération seront ignorés"
# #     )
# #     if uploaded_file is not None:
# #         df = pd.read_excel(uploaded_file)
# #         meter_names = df["Nom du meter"].tolist()
# #         if curve_type == "Index 15min":
# #             first_indext0 = [0] * len(meter_names)
# #         elif curve_type == "Index 24h T0":
# #             first_indext0 = df["1er index T0"].tolist()
# #         elif curve_type == "Index 24h T1/T2":
# #             first_indext1 = df["1er index T1"].tolist()
# #             first_indext2 = df["1er index T2"].tolist()
# #         elif curve_type == "Tout":
# #             first_indext0 = df["1er index T0"].tolist()
# #             first_indext1 = df["1er index T1"].tolist()
# #             first_indext2 = df["1er index T2"].tolist()
# #         else:
# #             raise SystemExit("Le type de courbe n'est pas correcte")

# #         st.write("Aperçu du fichier importé :")
# #         st.dataframe(df)

# # elif input_type == "Générer automatiquement X meters via un préfix":
# #     # Générer des noms automatiquement avec un préfixe
# #     meter_prefix = st.text_input("Préfixe pour les meters")
# #     count = st.number_input(
# #         "Nombre de meters à générer", min_value=1, value=5
# #     )

# #     meter_names = generate_names(meter_prefix, count)

# #     st.write("Meters générés :", meter_names)

# # Choix du range de dates
# start_date = pd.Timestamp("2024-10-18")
# end_date = pd.Timestamp("2024-10-21")

# date_range = (start_date, end_date)


# raise SystemExit('stop')
# # afficher_plot = st.checkbox("Afficher le graphique ?")
# # Bouton pour lancer la génération des fichiers
# # if st.button("Générer"):
# # generate_file(meter_names, metering_point_names, curve_type, date_range)

# # Générer les courbes de charge
# # print("test")
# load_curves = generate_electric_load_curve(
#     start_date, end_date, meter_names, points_per_day=96, noise_level=1.5
# )

# if curve_type == "Index 15min":
#     index_curves = load_curves.cumsum() + first_indext0
#     index_curves = index_curves.add_suffix("_15min")
# elif curve_type == "Index 24h T0":
#     index_curves = load_curves.cumsum() + first_indext0
#     index_curves = index_curves.asfreq("24h", method="pad")
#     index_curves = index_curves.add_suffix("_T0")
# elif curve_type == "Index 24h T1/T2":
#     index_curves = load_curves.cumsum()
#     index_curves = index_curves.asfreq("24h", method="pad")
#     index_curves = pd.concat(
#         [
#             index_curves.add_suffix("_T1") + first_indext1,
#             index_curves.add_suffix("_T2") + first_indext2,
#         ],
#         axis=1,
#     )
# elif curve_type == "Tout":
#     index_curves_15min = load_curves.cumsum() + first_indext0
#     index_curves_15min = index_curves_15min.add_suffix("_15min")

#     index_curves_24h = load_curves.cumsum()
#     index_curves_24h = index_curves_24h.asfreq("24h", method="pad")
#     index_curves_24h = pd.concat(
#         [
#             index_curves_24h.add_suffix("_T0") + first_indext0,
#             index_curves_24h.add_suffix("_T1") + first_indext2,
#             index_curves_24h.add_suffix("_T2") + first_indext2,
#         ],
#         axis=1,
#     )
# else:
#     raise SystemExit("Le type de courbe n'est pas correcte")
# # index_curves = load_curves.cumsum() + first_indext0

# if curve_type == "Tout":
#     generate_file(index_curves_15min)
#     generate_file(index_curves_24h)        
# else:
#     generate_file(index_curves)


# fig = plt.figure(figsize=(10, 6))
# fig.clf()
# ax = fig.gca()

# if curve_type == "Tout":
#     for column in index_curves_15min.columns:
#         plt.plot(
#             index_curves_15min.index, index_curves_15min[column], ".-", label=column
#         )
#     for column in index_curves_24h.columns:
#         plt.plot(
#             index_curves_24h.index, index_curves_24h[column], ".-", label=column
#         )
# else:
#     for column in index_curves.columns:
#         plt.plot(
#             index_curves.index, index_curves[column], ".-", label=column
#         )

# ax.set_xlabel("Date")
# ax.set_ylabel("Charge (kW)")
# ax.legend()
# ax.grid(True)
# # plt.xticks(rotation=45)
# fig.autofmt_xdate()
# fig.tight_layout()

# # st.pyplot(fig)

















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
        
        meter_names = []
        first_indext0 = []
        for elem in lines:
            meter_names.append(elem.split(',')[0])
            first_indext0.append(float(elem.split(',')[1]))
    elif curve_type == "Index 24h T0":
        lines = st.text_area(
            "Entrez les noms des meters, 1er index [kWh] (un par ligne)"
        ).split("\n")
        
        meter_names = []
        first_indext0 = []
        for elem in lines:
            meter_names.append(elem.split(',')[0])
            first_indext0.append(float(elem.split(',')[1]))
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
            # st.write("debut boucle lines")
            meter_names.append(elem.split(',')[0])
            first_indext1.append(float(elem.split(',')[1]))
            first_indext2.append(float(elem.split(',')[2]))
    elif curve_type == "Tout":
        lines = st.text_area(
            "Entrez les noms des meters, 1er index T0 [kWh], 1er index T1 [kWh], 1er index T2 [kWh] (un par ligne)"
        ).split("\n")
        
        meter_names = []
        first_indext0 = []
        first_indext1 = []
        first_indext2 = []
        for elem in lines:
            meter_names.append(elem.split(',')[0])
            first_indext0.append(float(elem.split(',')[1]))
            first_indext1.append(float(elem.split(',')[2]))
            first_indext2.append(float(elem.split(',')[3]))
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
start_date = pd.to_datetime(start_date).tz_localize('Europe/Zurich') #timestamp zurich

end_date = st.date_input("Date de fin", pd.Timestamp.today())
end_date = pd.to_datetime(end_date).tz_localize('Europe/Zurich') #timestamp zurich

date_range = (start_date, end_date)

afficher_plot = st.checkbox("Afficher le graphique ?")
# Bouton pour lancer la génération des fichiers
if st.button("Générer"):
    # generate_file(meter_names, metering_point_names, curve_type, date_range)

    # Générer les courbes de charge
    # print("test")
    # st.write("Debut")
    load_curves = generate_electric_load_curve(
        start_date, end_date, meter_names, points_per_day=96, noise_level=1.5
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
        generate_file(index_curves_15min,register_types)
        generate_file(index_curves_24h,register_types)        
    else:
        # st.write("Generate else")
        # st.dataframe(index_curves)
        generate_file(index_curves,register_types)

    if afficher_plot:
        # st.write("Afficher plot")
        # Afficher les courbes
        fig = plt.figure(figsize=(10, 6))
        fig.clf()
        ax = fig.gca()

        if curve_type == "Tout":
            for column in index_curves_15min.columns:
                plt.plot(
                    index_curves_15min.index, index_curves_15min[column], ".-", label=column
                )
            for column in index_curves_24h.columns:
                plt.plot(
                    index_curves_24h.index, index_curves_24h[column], ".-", label=column
                )
        else:
            for column in index_curves.columns:
                plt.plot(
                    index_curves.index, index_curves[column], ".-", label=column
                )

        ax.set_xlabel("Date")
        ax.set_ylabel("Charge (kW)")
        ax.legend()
        ax.grid(True)
        # plt.xticks(rotation=45)
        fig.autofmt_xdate()
        fig.tight_layout()

        st.pyplot(fig)
