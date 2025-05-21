
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="Cashflow Interactivo", layout="wide")

# --- Función principal ---
def generar_cashflow(inicio, fin, saldo_inicial, reducciones):
    fechas = pd.date_range(start=inicio, end=fin)
    cashflow = pd.DataFrame({'fecha': fechas})
    cashflow['dia'] = cashflow['fecha'].dt.day
    cashflow['mes'] = cashflow['fecha'].dt.month
    cashflow['dia_semana'] = cashflow['fecha'].dt.day_name()
    cashflow['saldo'] = np.nan
    cashflow['ingresos'] = 0.0
    cashflow['gastos'] = 0.0
    cashflow['descripcion_ingresos'] = ''
    cashflow['descripcion_gastos'] = ''
    cashflow.loc[0, 'saldo'] = saldo_inicial

    pagos = []
    for fecha in fechas:
        if fecha.day in [15, 30, 31]:
            ingreso_dia = fecha
            if ingreso_dia.weekday() == 5:
                ingreso_dia -= pd.Timedelta(days=1)
            elif ingreso_dia.weekday() == 6:
                ingreso_dia -= pd.Timedelta(days=2)
            if ingreso_dia in fechas and ingreso_dia not in pagos:
                idx = cashflow[cashflow['fecha'] == ingreso_dia].index
                cashflow.loc[idx, 'ingresos'] += 4280.00
                cashflow.loc[idx, 'descripcion_ingresos'] += 'Ingreso quincena'
                pagos.append(ingreso_dia)

    gastos_fijos = [
        ('Internet', 150, [4]), ('Disney', 160, [6]), ('ChatGPT', 160, [8]),
        ('Crunchyroll', 40, [10]), ('Xbox', 66, [12]), ('Préstamo banco', 650, [15]),
        ('Teléfono', 1050, [15]), ('Tarjeta', 700, [15, 30]), ('Overleaf', 160, [26]),
        ('Préstamo efectivo', 600, [30]), ('Universidad', 1300, [30]),
        ('Gasolina', 350, [1]), ('Vape', 210, [15])
    ]
    for dia_actual in fechas:
        for nombre, monto, dias in gastos_fijos:
            if dia_actual.day in dias:
                idx = cashflow[cashflow['fecha'] == dia_actual].index
                if not idx.empty:
                    cashflow.loc[idx, 'gastos'] += monto
                    cashflow.loc[idx, 'descripcion_gastos'] += f'{nombre}, '

    variables = {
        'Coca': 50, 'Salida': 130, 'Comida fuera': 100,
        'Comida': 50, 'Varios': 100, 'Waro': 250
    }

    total_usos = {k: 0 for k in variables}
    total_reducido = {k: 0 for k in variables}

    for i in range(0, len(cashflow), 2):
        base = variables['Coca']
        reduccion = base * reducciones.get('Coca', 0)
        cashflow.at[i, 'gastos'] += base - reduccion
        cashflow.at[i, 'descripcion_gastos'] += 'Coca, '
        total_usos['Coca'] += 1
        total_reducido['Coca'] += reduccion

    for nombre, dias in {
        'Salida': ['Sunday'], 'Comida fuera': ['Friday'], 'Comida': ['Tuesday'],
        'Varios': ['Monday'], 'Waro': ['Saturday', 'Sunday']
    }.items():
        for dia in dias:
            idx = cashflow['dia_semana'] == dia
            ocurrencias = idx.sum()
            base = variables[nombre]
            reduccion = base * reducciones.get(nombre, 0)
            cashflow.loc[idx, 'gastos'] += base - reduccion
            cashflow.loc[idx, 'descripcion_gastos'] += f'{nombre}, '
            total_usos[nombre] += ocurrencias
            total_reducido[nombre] += reduccion * ocurrencias

    for i in range(1, len(cashflow)):
        cashflow.at[i, 'saldo'] = (
            cashflow.at[i-1, 'saldo'] +
            cashflow.at[i, 'ingresos'] -
            cashflow.at[i, 'gastos']
        )

    cashflow['saldo'] = cashflow['saldo'].round(2)

    resumen = []
    for cat in variables:
        if total_usos[cat] > 0:
            original = variables[cat]
            nuevo = round(original - (total_reducido[cat] / total_usos[cat]), 2)
            resumen.append({
                'Categoría': cat,
                'Valor original': original,
                'Valor ajustado promedio': nuevo,
                'Total reducciones': round(total_reducido[cat], 2)
            })
    resumen_df = pd.DataFrame(resumen)

    dias_criticos = cashflow[cashflow['saldo'] < 500].copy()

    recomendaciones = []
    for _, row in dias_criticos.iterrows():
        if 'Waro' in row['descripcion_gastos']:
            recomendaciones.append((row['fecha'], 'Considera mover o reducir Waro'))
        if 'Varios' in row['descripcion_gastos']:
            recomendaciones.append((row['fecha'], 'Reduce gasto en Varios'))
        if 'Comida fuera' in row['descripcion_gastos']:
            recomendaciones.append((row['fecha'], 'Evita comer fuera este día'))
        if not any(x in row['descripcion_gastos'] for x in ['Waro', 'Varios', 'Comida fuera']):
            recomendaciones.append((row['fecha'], 'Revisa gastos de este día'))

    recomendaciones_df = pd.DataFrame(recomendaciones, columns=['Fecha', 'Recomendación'])

    return cashflow, resumen_df, dias_criticos, recomendaciones_df

# --- Interfaz Streamlit ---
st.title("📊 Cashflow Interactivo con Recomendaciones y Exportación")

col1, col2 = st.columns(2)
with col1:
    fecha_inicio = st.date_input("Fecha de inicio", value=datetime(2025, 5, 20))
    saldo_inicial = st.number_input("Saldo inicial", value=800.0, step=50.0)
with col2:
    fecha_fin = st.date_input("Fecha de fin", value=datetime(2025, 6, 30))

st.subheader("🔧 Reducción de gastos variables")
reducciones = {}
for var in ['Coca', 'Salida', 'Comida fuera', 'Comida', 'Varios', 'Waro']:
    reducciones[var] = st.slider(f"{var}", min_value=0.0, max_value=1.0, value=0.0, step=0.1)

if st.button("Simular Cashflow"):
    df, resumen, criticos, recomendaciones = generar_cashflow(fecha_inicio, fecha_fin, saldo_inicial, reducciones)

    st.subheader("📅 Flujo Detallado")
    st.dataframe(df[['fecha', 'ingresos', 'descripcion_ingresos', 'gastos', 'descripcion_gastos', 'saldo']], use_container_width=True)

    st.subheader("📉 Gráfico de saldo")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['fecha'], df['saldo'], marker='o')
    ax.axhline(0, color='red', linestyle='--')
    ax.fill_between(df['fecha'], df['saldo'], where=df['saldo'] < 500, color='orange', alpha=0.3)
    ax.set_title('Saldo diario')
    ax.set_ylabel('GTQ')
    ax.set_xlabel('Fecha')
    ax.grid(True)
    st.pyplot(fig)

    st.subheader("📌 Resumen de Reducciones")
    st.dataframe(resumen, use_container_width=True)

    st.subheader("🚨 Días Críticos (Saldo < 500)")
    st.dataframe(criticos[['fecha', 'saldo', 'gastos', 'descripcion_gastos']], use_container_width=True)

    st.subheader("💡 Recomendaciones")
    st.dataframe(recomendaciones, use_container_width=True)

    st.subheader("📤 Exportar a Excel")
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Flujo')
        resumen.to_excel(writer, index=False, sheet_name='Resumen')
        criticos.to_excel(writer, index=False, sheet_name='Dias_Criticos')
        recomendaciones.to_excel(writer, index=False, sheet_name='Recomendaciones')
    st.download_button(
        label="📥 Descargar Excel",
        data=buffer.getvalue(),
        file_name="cashflow_exportado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
