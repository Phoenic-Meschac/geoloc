import streamlit as st
import folium
from streamlit_folium import folium_static
import json
import os
from streamlit_js_eval import streamlit_js_eval

# Titre de l'application
st.title("Suivi en temps réel de plusieurs utilisateurs avec meilleure précision")

# Fichier pour stocker les positions (vous pouvez remplacer cela par une base de données)
positions_file = "user_positions.json"

# Fonction pour charger les positions à partir d'un fichier
def load_positions():
    # Vérifier si le fichier existe et qu'il n'est pas vide
    if os.path.exists(positions_file) and os.path.getsize(positions_file) > 0:
        with open(positions_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Si le fichier est corrompu ou illisible, on retourne un dictionnaire vide
                return {}
    return {}

# Fonction pour sauvegarder les positions dans un fichier
def save_positions(positions):
    with open(positions_file, "w") as f:
        json.dump(positions, f)

# Charger les positions actuelles
positions = load_positions()

# Exécuter du JavaScript pour obtenir la géolocalisation de l'utilisateur avec watchPosition
location_data = streamlit_js_eval(
    js_expressions="""
    new Promise((resolve, reject) => {
        const options = {
            enableHighAccuracy: true,  // Permet d'augmenter la précision
            timeout: 5000,             // Temps maximum avant de récupérer une nouvelle position
            maximumAge: 0              // Ne pas utiliser de position mise en cache
        };
        navigator.geolocation.watchPosition(
            (pos) => {
                resolve({
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                    accuracy: pos.coords.accuracy
                });
            },
            (err) => reject({
                code: err.code,
                message: err.message
            }),
            options
        );
    })
    """,
    key="geo"
)

# Vérifier si les données de localisation ont été récupérées
if isinstance(location_data, dict) and "latitude" in location_data and "longitude" in location_data:
    user_latitude = location_data["latitude"]
    user_longitude = location_data["longitude"]
    accuracy = location_data["accuracy"]

    # Filtrer en fonction de la précision (par exemple, on accepte uniquement si la précision est < 50 mètres)
    if accuracy <= 50:
        st.write(f"Précision de la position : {accuracy} mètres (acceptée)")
        
        # Générer un identifiant utilisateur unique (simple approche locale)
        user_id = st.experimental_get_query_params().get("user_id", ["default_user"])[0]

        # Sauvegarder la position actuelle de l'utilisateur
        positions[user_id] = {"latitude": user_latitude, "longitude": user_longitude}
        save_positions(positions)

        # Créer une carte centrée sur les positions moyennes des utilisateurs
        avg_lat = sum([pos["latitude"] for pos in positions.values()]) / len(positions)
        avg_lon = sum([pos["longitude"] for pos in positions.values()]) / len(positions)
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

        # Ajouter un marqueur pour chaque utilisateur
        for user, pos in positions.items():
            folium.Marker([pos["latitude"], pos["longitude"]], tooltip=f"Utilisateur: {user}").add_to(m)

        # Afficher la carte
        folium_static(m)
    else:
        st.warning(f"Précision de la position : {accuracy} mètres (trop faible)")
        
elif isinstance(location_data, dict) and "message" in location_data:
    # Gérer les erreurs de géolocalisation
    st.error(f"Erreur de géolocalisation : {location_data['message']}")
else:
    st.warning("En attente de la localisation...")

# Bouton pour réinitialiser les positions (utile pour le développement)
if st.button("Réinitialiser les positions"):
    save_positions({})
    st.experimental_rerun()
