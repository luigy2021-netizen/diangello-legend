import streamlit as st
import gspread
from datetime import datetime, date, time, timedelta
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Di'Angello Legend", page_icon="✂️")

SHEET_ID = "1N3QAuNXO0EckAOk5lb6ULmbk4nvs654dDJln-huHC1Q"

SERVICIOS = {
    "Corte Caballero": 30,
    "Corte Dama": 60,
    "Tinte Completo": 120,
    "Mechas / Highlights": 120,
    "Corte + Tinte Caballero": 90
}

HORA_APERTURA = time(10, 0)
HORA_CIERRE = time(17, 30)
COMIDA_INICIO = time(14, 0)
COMIDA_FIN = time(15, 0)

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

def dia_valido(fecha):
    return fecha.weekday() not in [0, 6]

def se_empalma(inicio1, fin1, inicio2, fin2):
    return inicio1 < fin2 and inicio2 < fin1

def formato_hora(dt):
    return dt.strftime("%I:%M %p")

def obtener_citas_del_dia(fecha):
    sheet = get_sheet()
    filas = sheet.get_all_values()
    citas = []

    for fila in filas[1:]:
        try:
            if len(fila) < 7:
                continue

            servicio = fila[3]
            duracion = int(fila[4])
            fecha_cita = fila[5]
            hora_cita = fila[6]

            if fecha_cita != str(fecha):
                continue

            inicio = datetime.strptime(
                f"{fecha_cita} {hora_cita}",
                "%Y-%m-%d %I:%M %p"
            )
            fin = inicio + timedelta(minutes=duracion)

            citas.append((inicio, fin))

        except:
            continue

    return citas

def horarios_disponibles(fecha, duracion):
    if not dia_valido(fecha):
        return []

    citas = obtener_citas_del_dia(fecha)
    disponibles = []

    inicio_dia = datetime.combine(fecha, HORA_APERTURA)
    cierre_dia = datetime.combine(fecha, HORA_CIERRE)
    comida_inicio = datetime.combine(fecha, COMIDA_INICIO)
    comida_fin = datetime.combine(fecha, COMIDA_FIN)

    actual = inicio_dia

    while actual < cierre_dia:
        fin_servicio = actual + timedelta(minutes=duracion)

        if fin_servicio <= cierre_dia:
            choca_comida = se_empalma(
                actual,
                fin_servicio,
                comida_inicio,
                comida_fin
            )

            choca_cita = any(
                se_empalma(actual, fin_servicio, cita_inicio, cita_fin)
                for cita_inicio, cita_fin in citas
            )

            if not choca_comida and not choca_cita:
                disponibles.append(formato_hora(actual))

        actual += timedelta(minutes=30)

    return disponibles

st.image(
    "https://raw.githubusercontent.com/luigy2021-netizen/diangello-legend/main/diangello.png",
    width=180
)

st.title("Di'Angello Legend ✂️")
st.write("Agenda tu cita de forma rápida y sencilla.")

st.markdown("### Servicios y duración")
for servicio, duracion in SERVICIOS.items():
    if duracion < 60:
        texto = f"{duracion} min"
    elif duracion == 60:
        texto = "1 hr"
    else:
        texto = f"{duracion // 60} hrs"
    st.write(f"• {servicio}: {texto}")

st.markdown("---")

servicio = st.selectbox("Servicio", list(SERVICIOS.keys()))
duracion = SERVICIOS[servicio]

fecha = st.date_input("Fecha", min_value=date.today())

if not dia_valido(fecha):
    st.error("Di’Angello no trabaja domingos ni lunes. Selecciona otro día.")
    st.stop()

horas = horarios_disponibles(fecha, duracion)

if not horas:
    st.warning("No hay horarios disponibles para ese servicio en esta fecha.")
    st.stop()

with st.form("formulario_cita", clear_on_submit=True):
    nombre = st.text_input("Nombre completo")
    whatsapp = st.text_input("WhatsApp (10 dígitos)", max_chars=10)
    hora = st.selectbox("Hora disponible", horas)
    notas = st.text_area("Comentarios adicionales")
    enviar = st.form_submit_button("Agendar cita")

if enviar:
    nombre = nombre.strip()
    whatsapp = whatsapp.strip()

    if not nombre:
        st.error("Escribe tu nombre.")
    elif len(whatsapp) != 10 or not whatsapp.isdigit():
        st.error("El WhatsApp debe tener exactamente 10 dígitos.")
    elif hora not in horarios_disponibles(fecha, duracion):
        st.error("Ese horario acaba de ocuparse. Elige otro.")
    else:
        try:
            sheet = get_sheet()
            sheet.append_row([
                datetime.now().strftime("%Y%m%d%H%M%S"),
                nombre,
                whatsapp,
                servicio,
                duracion,
                str(fecha),
                hora,
                "Pendiente",
                notas
            ])
            st.success("✅ Cita guardada correctamente.")
        except Exception as e:
            st.error(f"Error: {e}")
