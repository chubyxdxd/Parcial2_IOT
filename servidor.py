import streamlit as st
import pandas as pd
import mysql.connector
import time
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Centro de Mando IoT", layout="wide", page_icon="📡")

def conectar_db():
    return mysql.connector.connect(
        host="192.168.1.112",
        user="fabricio",
        password="efenomas", 
        database="iot_telemetry"  # Actualizado al nuevo nombre de tu BD
    )

def generar_resumen_usuarios():
    try:
        conn = conectar_db()
        # --- CONSULTA RELACIONAL ADAPTADA A SENSORES E IA ---
        query = """
            SELECT u.nombre_usuario, COUNT(c.idu) as total_registros
            FROM (
                SELECT idu FROM dht22_data
                UNION ALL
                SELECT idu FROM mpu_data
                UNION ALL
                SELECT idu FROM ai_inference
            ) AS c
            JOIN usuarios u ON c.idu = u.id
            GROUP BY u.id, u.nombre_usuario
        """
        df_usuarios = pd.read_sql(query, conn)
        conn.close()

        if not df_usuarios.empty:
            st.subheader("Tráfico de Datos por Operador")
            
            fig = px.pie(
                df_usuarios, 
                values='total_registros', 
                names='nombre_usuario', 
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Tealgrn
            )
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Ver tabla de aportes por usuario"):
                st.dataframe(df_usuarios.sort_values('total_registros', ascending=False), use_container_width=True)
        else:
            st.info("No hay datos registrados en el sistema todavía.")
            
    except Exception as e:
        st.error(f"Error al cargar el resumen de usuarios: {e}")

def generar_dashboard_clima():
    try:
        conn = conectar_db()
        query = "SELECT id, temp_amb, hum_amb, timed FROM dht22_data ORDER BY timed ASC"
        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            df['timed'] = pd.to_datetime(df['timed'])
            ultima_temp = df['temp_amb'].iloc[-1]
            ultima_hum = df['hum_amb'].iloc[-1]
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Registros de Clima", len(df))
            m2.metric("Temperatura Actual", f"{ultima_temp:.1f} °C")
            m3.metric("Humedad Actual", f"{ultima_hum:.1f} %")

            st.subheader("Evolución del Clima (DHT22)")
            # Mostrar los últimos 50 registros para no saturar la gráfica
            df_recent = df.tail(50)
            st.line_chart(df_recent.set_index('timed')[['temp_amb', 'hum_amb']])
            
            with st.expander("Historial completo (DHT22)"):
                st.dataframe(df.sort_values('timed', ascending=False))
        else:
            st.warning("Esperando datos del DHT22...")
            
    except Exception as e:
        st.error(f"Error: {e}")

def generar_dashboard_mpu():
    try:
        conn = conectar_db()
        query = "SELECT id, pitch, roll, temp_mpu, timed FROM mpu_data ORDER BY timed ASC"
        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            df['timed'] = pd.to_datetime(df['timed'])
            ultimo_pitch = df['pitch'].iloc[-1]
            ultimo_roll = df['roll'].iloc[-1]
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Registros de Movimiento", len(df))
            m2.metric("Pitch Actual", f"{ultimo_pitch:.2f}°")
            m3.metric("Roll Actual", f"{ultimo_roll:.2f}°")

            col_izq, col_der = st.columns(2)
            df_recent = df.tail(50)

            with col_izq:
                st.subheader("Inclinación: Pitch vs Roll")
                st.line_chart(df_recent.set_index('timed')[['pitch', 'roll']])
            
            with col_der:
                st.subheader("Temperatura del Chip MPU")
                st.area_chart(df_recent.set_index('timed')['temp_mpu'])
            
            with st.expander("Historial completo (MPU6050)"):
                st.dataframe(df.sort_values('timed', ascending=False))
        else:
            st.warning("Esperando datos del MPU6050...")
            
    except Exception as e:
        st.error(f"Error: {e}")

def generar_dashboard_ia():
    try:
        conn = conectar_db()
        query = "SELECT id, clase_detectada, accuracy, timed FROM ai_inference ORDER BY timed ASC"
        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            df['timed'] = pd.to_datetime(df['timed'])
            ultima_clase = df['clase_detectada'].iloc[-1]
            ultimo_acc = df['accuracy'].iloc[-1]
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Inferencias Totales", len(df))
            m2.metric("Última Clase Detectada", ultima_clase)
            m3.metric("Última Precisión (Accuracy)", f"{ultimo_acc * 100:.2f} %")

            col_izq, col_der = st.columns(2)
            
            with col_izq:
                st.subheader("Frecuencia de Clases")
                conteo_clases = df['clase_detectada'].value_counts().reset_index()
                conteo_clases.columns = ['Clase', 'Cantidad']
                fig_bar = px.bar(conteo_clases, x='Clase', y='Cantidad', color='Clase', title="Detecciones Acumuladas")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_der:
                st.subheader("Evolución de Accuracy")
                df_recent = df.tail(30)
                st.line_chart(df_recent.set_index('timed')['accuracy'])
            
            with st.expander("Historial completo (IA)"):
                st.dataframe(df.sort_values('timed', ascending=False))
        else:
            st.warning("Esperando inferencias de la Raspberry Pi 5...")
            
    except Exception as e:
        st.error(f"Error: {e}")


# --- INTERFAZ PRINCIPAL ---
st.title("🛰️ Dashboard Control IoT - Telemetría")

# Pestañas
tabs = st.tabs(["Resumen Global", "Clima (DHT22)", "Inclinación (MPU6050)", "Inferencia IA (Raspi 5)"])

with tabs[0]:
    generar_resumen_usuarios()
with tabs[1]:
    generar_dashboard_clima()
with tabs[2]:
    generar_dashboard_mpu()
with tabs[3]:
    generar_dashboard_ia()

# Bucle de actualización (Estilo Streamlit correcto)
time.sleep(2)
st.rerun()	
