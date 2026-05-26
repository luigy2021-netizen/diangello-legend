import os
from datetime import date, datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# 1. Configuración de la página e interfaz limpia
st.set_page_config(
    page_title="Di'Angello Legend",
    page_icon="✂️",
    layout="centered"
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# 2. Conexión con Google Sheets
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(base_dir, "credentials.json")

    creds = Credentials.from_service_account_file(
        cred_path,
        scopes=scopes
    )

    client = gspread.authorize(creds)
    sheet = client.open("Citas_DiAngello").sheet1
    return sheet

# 3. Encabezado principal
st.image(
    "https://raw.githubusercontent.com/luigy2021-netizen/diangello-legend/main/diangello.png",
    width=200
)
st.title("Di'Angello Legend")
st.subheader("✂️ Salón de Belleza & Barbería")
st.markdown("---")

# 4. Diccionario con tus servicios y precios
SERVICIOS = {
    "Corte Caballero": 250,
    "Corte Dama": 350,
    "Tinte Completo": 600,
    "Mechas / Highlights": 800,
    "Corte + Tinte Caballero": 450
}

# 5. Mostrar servicios
st.markdown("### 📋 Nuestros Servicios y Precios")
cols = st.columns(2)
for i, (servicio, precio) in enumerate(SERVICIOS.items()):
    col_actual = cols[0] if i % 2 == 0 else cols[1]
    col_actual.markdown(f"**{servicio}** — `${precio} MXN`")

st.markdown("---")

# 6. Formulario de citas
st.markdown("### 📅 Agenda tu cita")

with st.form("formulario_cita", clear_on_submit=True):
    nombre = st.text_input("Tu nombre completo:")
    whatsapp = st.text_input("Tu WhatsApp (a 10 dígitos):", max_chars=20)
    servicio_seleccionado = st.selectbox("Selecciona el servicio:", list(SERVICIOS.keys()))
    fecha = st.date_input("Fecha de tu cita:", min_value=date.today())

    horas_disponibles = [
        "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM",
        "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM"
    ]
    hora = st.selectbox("Hora de tu cita:", horas_disponibles)
    notas = st.text_area("Notas adicionales (opcional):")

    boton_agendar = st.form_submit_button("Agendar Cita")

# 7. Lógica de registro
if boton_agendar:
    nombre = nombre.strip()
    whatsapp = "".join(filter(str.isdigit, whatsapp.strip()))

    if not nombre:
        st.error("⚠️ Escribe tu nombre completo.")
    elif len(whatsapp) != 10:
        st.error("⚠️ El WhatsApp debe tener exactamente 10 dígitos.")
    else:
        try:
            precio_final = SERVICIOS[servicio_seleccionado]
            sheet = get_sheet()

            id_cita = datetime.now().strftime("%Y%m%d%H%M%S")

            nueva_fila = [
                id_cita,
                nombre,
                whatsapp,
                servicio_seleccionado,
                precio_final,
                str(fecha),
                hora,
                "Pendiente",
                "",
                notas
            ]

            sheet.append_row(nueva_fila)

            st.success(
                f"¡Gracias {nombre}! Tu cita para **{servicio_seleccionado}** "
                f"(${precio_final} MXN) el día {fecha} a las {hora} ha sido agendada con éxito."
            )

            mensaje_wa = (
                f"¡Hola! Confirmación de cita en Di'Angello Legend:\n\n"
                f"👤 Cliente: {nombre}\n"
                f"✂️ Servicio: {servicio_seleccionado}\n"
                f"💵 Precio: ${precio_final} MXN\n"
                f"📅 Fecha: {fecha}\n"
                f"⏰ Hora: {hora}"
            )
            mensaje_codificado = mensaje_wa.replace(" ", "%20").replace("\n", "%0A")
            url_whatsapp = f"https://wa.me/52{whatsapp}?text={mensaje_codificado}"

            st.markdown(
                f"[💬 Haz clic aquí para enviar la confirmación por WhatsApp]({url_whatsapp})"
            )

        except Exception as e:
            st.error(f"❌ Hubo un problema al guardar tu cita. Error: {e}")

