import folium
import numpy as np
import streamlit as st
from shapely.geometry import Polygon, MultiPolygon
import string
from streamlit_folium import folium_static

def gerar_celula(lat, lon, azimute, alcance, abertura=120):
    pontos = []
    for angulo in np.linspace(azimute - abertura / 2, azimute + abertura / 2, num=30):
        angulo_rad = np.radians(angulo)
        dlat = (alcance / 111) * np.cos(angulo_rad)
        dlon = (alcance / (111 * np.cos(np.radians(lat)))) * np.sin(angulo_rad)
        pontos.append((lat + dlat, lon + dlon))
    pontos.append((lat, lon))  # Fechar a célula
    return pontos

def gerar_rotulo_coluna(indice):
    letras = string.ascii_uppercase
    rotulo = ""
    while indice >= 0:
        rotulo = letras[indice % 26] + rotulo
        indice = (indice // 26) - 1
    return rotulo

def gerar_grelha(area_coberta, tamanho_quadricula):
    min_lat, min_lon, max_lat, max_lon = area_coberta.bounds
    linhas = []
    etiquetas = []
    
    delta_lat = tamanho_quadricula / 111000  # Conversão de metros para graus de latitude
    delta_lon = lambda lat: tamanho_quadricula / (111000 * np.cos(np.radians(lat)))  # Ajuste da longitude
    
    lat_range = np.arange(max_lat, min_lat, -delta_lat)
    lon_range = np.arange(min_lon, max_lon, delta_lon((max_lat + min_lat) / 2))

    for lon in lon_range:
        linhas.append([(min_lat, lon), (max_lat, lon)])
    for lat in lat_range:
        linhas.append([(lat, min_lon), (lat, max_lon)])

    perimetro = [(min_lat, min_lon), (min_lat, max_lon), (max_lat, max_lon), (max_lat, min_lon), (min_lat, min_lon)]

    for row_index, lat in enumerate(lat_range[:-1]):
        for col_index, lon in enumerate(lon_range[:-1]):
            coluna_label = gerar_rotulo_coluna(col_index)
            etiqueta = f"{coluna_label}{row_index + 1}"
            etiquetas.append(((lat - delta_lat / 2, lon + delta_lon(lat) / 2), etiqueta))

    return linhas, etiquetas, perimetro

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("_Multi Cell View_")
    st.sidebar.markdown(":blue[**_©2025 NAIIC CTer Santarém_**]")
    
    cores = ["blue", "red", "green"]
    
    lat_default = 39.2369
    lon_default = -8.6807
    azimute_default = 40
    alcance_default = 3
    tamanho_quadricula_default = 500

    with st.sidebar.expander("Configuração Geral", expanded=True):
        mapa_tipo = st.selectbox("Tipo de mapa", ["Padrão", "Satélite", "OpenStreetMap", "Terreno"])
        mostrar_grelha = st.toggle("Mostrar Grelha")
        tamanho_quadricula = st.slider("Tamanho da Quadricula (m)", 200, 1000, tamanho_quadricula_default, step=50)
        cor_grelha = st.color_picker("Cor da Grelha e Rótulos", "#FFA500")
    
    with st.sidebar.expander("Configuração das Células", expanded=True):
        alcance = st.slider("Alcance Geral (km)", 1, 20, alcance_default)
    
    celulas = []
    area_coberta = None

    for i in range(3):
        with st.sidebar.expander(f"Célula {i+1}", expanded=(i == 0)):
            ativo = st.checkbox(f"Ativar Célula {i+1}", value=(i == 0))
            if ativo:
                col1, col2 = st.columns(2)
                with col1:
                    lat = st.number_input(f"Lat {i+1}", value=lat_default, format="%.6f", key=f"lat_{i}")
                with col2:
                    lon = st.number_input(f"Lon {i+1}", value=lon_default, format="%.6f", key=f"lon_{i}")
                azimute = st.slider(f"Azimute {i+1}", 0, 360, azimute_default + i * 120, key=f"azimute_{i}")
                celulas.append((lat, lon, azimute, cores[i]))
                poligono = Polygon(gerar_celula(lat, lon, azimute, alcance))
                area_coberta = poligono if area_coberta is None else area_coberta.union(poligono)

    tiles_dict = {
        "Padrão": "CartoDB positron",
        "Satélite": "Esri WorldImagery",
        "OpenStreetMap": "OpenStreetMap",
        "Terreno": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
    }
    
    mapa = folium.Map(location=[lat_default, lon_default], zoom_start=13, tiles=tiles_dict[mapa_tipo], attr="Esri WorldTopoMap")
    
    for lat, lon, azimute, cor in celulas:
        folium.Marker([lat, lon], tooltip=f"BTS {lat}, {lon}").add_to(mapa)
        celula_coords = gerar_celula(lat, lon, azimute, alcance)
        folium.Polygon(locations=celula_coords, color=cor, fill=True, fill_color=cor, fill_opacity=0.3).add_to(mapa)

    if mostrar_grelha and area_coberta is not None:
        grelha, etiquetas, perimetro = gerar_grelha(area_coberta, tamanho_quadricula)
        for linha in grelha:
            folium.PolyLine(linha, color=cor_grelha, weight=2, opacity=0.9).add_to(mapa)
        for (pos, label) in etiquetas:
            folium.Marker(pos, icon=folium.DivIcon(html=f'<div style="font-size: 8pt; color: {cor_grelha};">{label}</div>')).add_to(mapa)
        folium.PolyLine(perimetro, color=cor_grelha, weight=4, opacity=1).add_to(mapa)

    if area_coberta:
        mapa.fit_bounds(area_coberta.bounds)

    folium.LayerControl().add_to(mapa)
    
    st.markdown(
        """
        <style>
            iframe {
                width: 100% !important;
                height: calc(100vh - 20px) !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    folium_static(mapa)

if __name__ == "__main__":
    main()
