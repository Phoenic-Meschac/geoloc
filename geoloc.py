import streamlit as st
import asyncio
import websockets
import json
import folium
from streamlit_folium import folium_static
from streamlit_js_eval import streamlit_js_eval

# Titre de l'application
st.title("Suivi des utilisateurs en temps réel")

# Fonction pour se connecter au serveur WebSocket et envoyer/recevoir des positions
async def websocket_client():
    uri = "ws://localhost:6789"  # Adresse du serveur WebSocket
    async with websockets.connect(uri) as websocket:
        # Exécuter du JavaScript pour obtenir la géolocalisation de l'utilisateur
        location_data = streamlit_js_eval(
            js_expressions="""
            new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    (pos) => {
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
        
        if isinstance(location_data, dict) and "latitude" in location_data and "longitude" in location_data:
            user_latitude = location_data["latitude"]
            user_longitude = location_data["longitude"]

            # Générer un identifiant utilisateur unique
            user_id = st.experimental_get_query_params().get("user_id", ["default_user"])[0]

            # Envoyer la position de l'utilisateur au serveur WebSocket
            position_message = json.dumps({
                'user_id': user_id,
                'latitude': user_latitude,
                'longitude': user_longitude
            })
            await websocket.send(position_message)

            # Recevoir la position des autres utilisateurs
            positions_data = await websocket.recv()
            return json.loads(positions_data)

        else:
            st.warning("En attente de la localisation...")
            return {}

# Affichage de la carte avec les positions des utilisateurs
async def display_map():
    positions = await websocket_client()

    if positions:
        # Calculer la position centrale de la carte (par exemple, la moyenne des positions)
        avg_lat = sum([pos["latitude"] for pos in positions.values()]) / len(positions)
        avg_lon = sum([pos["longitude"] for pos in positions.values()]) / len(positions)

        # Créer une carte centrée sur la position moyenne
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

        # Ajouter des marqueurs pour chaque utilisateur
        for user, pos in positions.items():
            folium.Marker([pos["latitude"], pos["longitude"]], tooltip=f"Utilisateur: {user}").add_to(m)

        # Afficher la carte
        folium_static(m)

# Lancer l'affichage de la carte
asyncio.run(display_map())
