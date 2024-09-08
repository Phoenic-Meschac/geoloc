import streamlit as st
import folium
from streamlit_folium import folium_static
from streamlit_js_eval import streamlit_js_eval

# Titre de l'application
st.title("Carte avec géolocalisation corrigée")

# Exécuter du JavaScript pour obtenir la géolocalisation de l'utilisateur
location_data = streamlit_js_eval(
    js_expressions="""
    new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                // Extraire uniquement les propriétés latitude et longitude
                resolve({
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude
                });
            },
            (err) => reject({
                code: err.code,
                message: err.message
            })
        );
    })
    """,
    key="geo"
)

# Vérifier si les données de localisation ont été récupérées
if isinstance(location_data, dict) and "latitude" in location_data and "longitude" in location_data:
    latitude = location_data["latitude"]
    longitude = location_data["longitude"]

    # Afficher les coordonnées récupérées
    st.write(f"Latitude: {latitude}")
    st.write(f"Longitude: {longitude}")

    # Créer une carte centrée sur les coordonnées récupérées
    m = folium.Map(location=[latitude, longitude], zoom_start=15)

    # Ajouter un marqueur à la position actuelle
    folium.Marker([latitude, longitude], tooltip="Vous êtes ici").add_to(m)

    # Afficher la carte avec le marqueur
    folium_static(m)
elif isinstance(location_data, dict) and "message" in location_data:
    # Gérer les erreurs de géolocalisation
    st.error(f"Erreur de géolocalisation : {location_data['message']}")
else:
    st.warning("En attente de la localisation...")
