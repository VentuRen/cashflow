# %% [markdown]
# # 📊 Cashflow Interactivo con Exportación Completa y Recomendaciones

# %%

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output
import io
from IPython.display import FileLink


# %%

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
            if fecha.weekday() == 5:
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


# %%

fecha_inicio = widgets.DatePicker(description='Inicio', value=datetime(2025, 5, 20))
fecha_fin = widgets.DatePicker(description='Fin', value=datetime(2025, 6, 30))
saldo_inicial = widgets.BoundedFloatText(value=800.0, min=0, max=10000, step=50, description='Saldo inicial')

sliders = {
    cat: widgets.FloatSlider(value=0, min=0, max=1, step=0.1, description=cat)
    for cat in ['Coca', 'Salida', 'Comida fuera', 'Comida', 'Varios', 'Waro']
}

boton = widgets.Button(description="Simular")
output = widgets.Output()
excel_output = widgets.Output()

def simular(b):
    reducciones = {k: s.value for k, s in sliders.items()}
    df, resumen_df, criticos_df, recomendaciones_df = generar_cashflow(
        fecha_inicio.value, fecha_fin.value, saldo_inicial.value, reducciones)

    with output:
        clear_output(wait=True)
        pd.set_option('display.max_colwidth', 1000)
        display(df[['fecha', 'ingresos', 'descripcion_ingresos', 'gastos', 'descripcion_gastos', 'saldo']])
        plt.figure(figsize=(12, 5))
        plt.plot(df['fecha'], df['saldo'], marker='o', linestyle='-', label='Saldo diario')
        plt.axhline(0, color='red', linestyle='--', label='Límite de sobregiro')
        plt.fill_between(df['fecha'], df['saldo'], where=df['saldo'] < 500, color='orange', alpha=0.3, label='Bajo balance')
        plt.title('Cashflow Interactivo - Flujo Expandido')
        plt.xlabel('Fecha')
        plt.ylabel('Saldo (GTQ)')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
        print("\n📌 Resumen de Reducciones Aplicadas:")
        display(resumen_df)
        print("\n🚨 Días Críticos (Saldo < 500):")
        display(criticos_df[['fecha', 'saldo', 'gastos', 'descripcion_gastos']])
        print("\n💡 Recomendaciones:")
        display(recomendaciones_df)

    with excel_output:
        clear_output(wait=True)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Flujo')
            resumen_df.to_excel(writer, index=False, sheet_name='Resumen')
            criticos_df.to_excel(writer, index=False, sheet_name='Dias_Criticos')
            recomendaciones_df.to_excel(writer, index=False, sheet_name='Recomendaciones')
        buffer.seek(0)
        with open("cashflow_exportado_final.xlsx", "wb") as f:
            f.write(buffer.read())
        display(FileLink("cashflow_exportado_final.xlsx"))

boton.on_click(simular)
display(widgets.VBox([fecha_inicio, fecha_fin, saldo_inicial, *sliders.values(), boton, output, excel_output]))



