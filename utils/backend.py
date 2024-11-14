# Importación de módulos y librerías necesarios
import streamlit as st
import pandas as pd
import copy
import io
import json

# Función para comprobar la extensión de un archivo cargado
def check_extension(uploaded_data):
    # Realiza una copia profunda de los datos cargados para no modificar los datos originales
    copied_data = copy.deepcopy(uploaded_data)
    
    # Comprueba si la extensión del archivo es .xlsx (Excel)
    if copied_data.name.endswith('xlsx'):
        pass  # Puede hacer algo con el archivo, pero el código no muestra qué hacer
        # st.markdown(f"##### :heavy_check_mark: _:green[{copied_data.name}]_ subido correctamente ")
    else:
        # Muestra un mensaje de error si el formato del archivo no es válido
        st.error("Formato de archivo no válido. Por favor, carga un archivo Excel.")
        st.stop()  # Detiene la ejecución de la aplicación Streamlit si se encuentra un archivo con formato incorrecto

# Función para verificar si un DataFrame contiene las columnas esperadas
def check_dataframe_columns(uploaded_data):
    # Realiza una copia profunda de los datos cargados para no modificar los datos originales
    copied_data = copy.deepcopy(uploaded_data)
    
    # Lee el archivo Excel y carga su contenido en un DataFrame
    df = pd.read_excel(copied_data)
    
    # Obtiene la lista de nombres de columnas del DataFrame
    df_columns = df.columns.tolist()

    # ruta del JSON que contiene las columnas esperadas
    json_filename = 'json_files/database_names.json'
    
    # Abre y carga el contenido del archivo JSON en un diccionario
    with open(json_filename, 'r') as json_file:
        data_dictionary = json.load(json_file)
    
    # Obtiene la lista de columnas esperadas del diccionario cargado
    expected_columns = data_dictionary['expected_columns']

    # Encuentra las columnas que faltan en el DataFrame comparando con las columnas esperadas
    missing_columns = set(expected_columns) - set(df_columns)

    # Encuentra las columnas adicionales que no se esperaban en el DataFrame
    extra_columns = set(df_columns) - set(expected_columns)

    # Verifica si el DataFrame contiene exactamente las mismas columnas que se esperaban
    if len(missing_columns) == 0 and len(extra_columns) == 0:
        pass  # si cumple con las columnas se sigue con la ejecución normal
    else:
        # Muestra un mensaje de error si el DataFrame no contiene las mismas columnas que se esperaban
        st.error("El DataFrame no contiene exactamente las mismas columnas.")

        # Comprueba si hay columnas faltantes o columnas adicionales y muestra un mensaje de advertencia
        if len(missing_columns) > 0 or len(extra_columns) > 0:
            warning_message = ""  # Inicializa una cadena de advertencia vacía

            if len(missing_columns) > 0:
                # Si hay columnas faltantes, agrega un mensaje indicando cuáles son
                warning_message += f"Columnas faltantes: \n\n{list(missing_columns)}\n\n"

            if len(extra_columns) > 0:
                # Si hay columnas adicionales, agrega un mensaje indicando cuáles son
                warning_message += f"Columnas adicionales: \n\n{list(extra_columns)}"

            # Muestra una advertencia en la aplicación Streamlit con el mensaje construido
            st.warning(warning_message)

            # Detiene la ejecución de la aplicación Streamlit si las columnas no coinciden
            st.stop()

#----------------------------------------------------
# Aqui empieza la primera optimizacion
#----------------------------------------------------
# la funcion transform_dataframe puede vectorizarse para ahorrar espacio

def transform_dataframe(df):
    # Crear una copia del DataFrame para mantener el original sin cambios
    df_copy = df.copy()
    
    # Definir columnas de demanda mensual solo una vez
    demand_cols = [f'demanda_mes{i}' for i in range(1, 13)]
    
    # Variables auxiliares
    precio = df['precio_uni/bulto']
    costo = df['costo_uni/bulto']
    demanda = df[demand_cols]
    
    # Calcular todas las nuevas columnas de forma vectorizada
    df_copy['unidades_vendidas'] = demanda.sum(axis=1)
    df_copy['bultos_vendidos'] = df_copy['unidades_vendidas'] / df['empaque']
    df_copy['margen_utilidad/ventas'] = (precio - costo) / precio
    df_copy['ventas_totales'] = df_copy['bultos_vendidos'] * precio
    df_copy['ventas_al_costo'] = df_copy['bultos_vendidos'] * costo
    df_copy['margen_bruto'] = df_copy['bultos_vendidos'] * (precio - costo)
    df_copy['valor_inv_prom_bultos'] = df['inv_prom/bultos'] * costo
    df_copy['rotacion'] = df_copy['ventas_al_costo'] / df_copy['valor_inv_prom_bultos']
    df_copy['meses_inv'] = 12 / df_copy['rotacion']
    df_copy['prom_bultos_desp/mes'] = demanda.mean(axis=1)
    df_copy['cubicaje_inv_prom'] = df['cubicaje/tarima'] * (df['inv_final/bultos'] / df['bultos/tarima'])
    
    return df_copy

#------------------------------------------------
# No he realizado mas cambios, pero escojo el codigo minimo para correr el calculo
#------------------------------------------------

# Función para aplicar estilos y formato a un DataFrame
def style_dataframe(df):
    df = df.copy()  # Realiza una copia del DataFrame original para no modificarlo

    # ruta al JSON que contiene los nombres de las columnas
    json_filename = 'json_files/database_names.json'
    
    # Carga el contenido del archivo JSON en un diccionario
    with open(json_filename, 'r') as json_file:
        data_dictionary = json.load(json_file)

    # Divide las columnas del DataFrame en dos grupos: esperadas y calculadas
    expected_columns = data_dictionary['expected_columns']
    calculated_columns = data_dictionary['calculated_columns']

    # Define los estilos para cada grupo de columnas
    column_styles = {
        col: {'background-color': 'black', 'color': 'lawngreen'} for col in expected_columns
    }
    column_styles.update({
        col: {'background-color': 'black', 'color': 'red'} for col in calculated_columns
    })

    # Crea una copia del DataFrame con los estilos aplicados
    styled_df = df.style

    # Aplica formato a columnas específicas del DataFrame
    cubicaje_format = "{:.2f} m³"
    currency_format = "$ {:,.2f}"
    integer_format = "{:.0f}"
    percent_format = "{:.0%}"  
    decimal_format = "{:.2f}"

    styled_df = styled_df.format({
        'cubicaje/tarima': cubicaje_format,
        'cubicaje_inv_prom': cubicaje_format,
        'precio_uni/bulto': currency_format,
        'costo_uni/bulto': currency_format,
        'ventas_totales': currency_format,
        'ventas_al_costo': currency_format,
        'margen_bruto': currency_format,
        'valor_inv_prom_bultos': currency_format,
        'empaque': integer_format,
        'bultos/tarima': integer_format,
        'demanda_mes1': integer_format,
        'demanda_mes2': integer_format,
        'demanda_mes3': integer_format,
        'demanda_mes4': integer_format,
        'demanda_mes5': integer_format,
        'demanda_mes6': integer_format,
        'demanda_mes7': integer_format,
        'demanda_mes8': integer_format,
        'demanda_mes9': integer_format,
        'demanda_mes10': integer_format,
        'demanda_mes11': integer_format,
        'demanda_mes12': integer_format,
        't_entrega_prom': integer_format,
        'inv_final/bultos': integer_format,
        'inv_prom/bultos': integer_format,
        'inv_trans/bultos': integer_format,
        'unidades_vendidas': integer_format,
        'bultos_vendidos': integer_format,
        'prom_bultos_desp/mes': integer_format,
        'factor_escazes': percent_format,
        'margen_utilidad/ventas': percent_format,
        'rotacion': decimal_format,
        'meses_inv': decimal_format
    })
    
    # Aplica estilos a las columnas basados en los grupos definidos
    for column, styles in column_styles.items():
        styled_df = styled_df.set_properties(subset=column, **styles)
    
    # Devuelve el DataFrame con estilos y formato aplicados
    return styled_df

# Función para obtener un DataFrame transformado a partir de una tabla Excel
def get_transformed_dataframe(table):
    if table is None:
        st.warning("No hay datos disponibles para transformar.")
        return pd.DataFrame()  # Return an empty DataFrame

    # Read the Excel file and load its contents into a DataFrame
    df = pd.read_excel(table, engine='openpyxl')
    
    # Apply a transformation function (transform_dataframe) to the DataFrame
    df_transformed = transform_dataframe(df)
    
    # Return the transformed DataFrame
    return df_transformed

# Función para obtener un DataFrame con estilos a partir de un DataFrame transformado
def get_styled_dataframe(df_transformed):
    # Aplica estilos al DataFrame transformado utilizando la función 'style_dataframe'
    df_styled = style_dataframe(df_transformed)
    
    # Devuelve el DataFrame con estilos aplicados
    return df_styled

# Función para exportar un DataFrame a un archivo CSV y devolverlo en formato binario
def export_csv(df):
    # Convierte el DataFrame a un archivo CSV con índice incluido y lo codifica en formato 'utf-8'
    return df.to_csv(index=True).encode('utf-8')

# Función para exportar un DataFrame a un archivo Excel y devolverlo en formato binario
def export_excel(df):
    # Crea un objeto de salida en formato binario
    output = io.BytesIO()
    
    # Crea un escritor de Excel utilizando el motor 'openpyxl'
    writer = pd.ExcelWriter(output, engine='openpyxl')
    
    # Guarda el DataFrame en una hoja de Excel llamada 'Base transformada' con índice incluido
    df.to_excel(writer, sheet_name='Base transformada', index=True)
    
    # Cierra el escritor y ajusta la posición del objeto de salida al principio
    writer.close()
    output.seek(0)
    
    # Devuelve el objeto de salida en formato binario
    return output

# Función para mostrar botones de descarga de datos en una aplicación Streamlit
def download_dataframe(df, name="Base"):
    # Exporta el DataFrame a formatos CSV y Excel
    csv = export_csv(df)
    excel = export_excel(df)

    # Muestra una leyenda en la aplicación Streamlit
    st.caption("Exportar datos:")
    
    # Crea botones de descarga para CSV y Excel en la aplicación Streamlit
    st.download_button(
        label="Descargar como CSV",
        data=csv,
        file_name=f'{name}.csv'
    )

    st.download_button(
        label="Descargar como Excel",
        data=excel,
        file_name=f'{name}.xlsx'
    )


