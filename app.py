import streamlit as st
import pandas as pd
import io
from datetime import datetime

# 🔧 Cambiar título de pestaña
st.set_page_config(
    page_title="Mosare App",
    page_icon="🩺",
)

st.title("🎯 Filtro de pacientes Mosare")


# Subida de archivos
aten_file = st.file_uploader("📄 Sube el archivo AtenMedxServ", type=["txt"])
resul_file = st.file_uploader("📄 Sube el archivo ResulExam_PatCli", type=["txt"])
cartera_file = st.file_uploader("📄 Sube el archivo CarteraVisare", type=["txt"])

# Diccionario de IPRES
ipres_dict = {
    "478": "CAP III ALFREDO PIAZZA ROBERTS",
    "646": "CAP III EL AGUSTINO",
    "447": "CAP III HUAYCAN",
    "481": "CAP III INDEPENDENCIA",
    "019": "CENTRO MEDICO ANCUE",
    "020": "CENTRO MEDICO CASAPALCA",
    "405": "HOSPITAL I AURELIO DIAZ UFANO Y PERAL",
    "404": "HOSPITAL I JORGE VOTO BERNALLES CORPANCHO",
    "403": "HOSPITAL II CLINICA GERIATRICA SAN ISIDRO LABRADOR",
    "017": "HOSPITAL II RAMON CASTILLA",
    "008": "HOSPITAL II VITARTE",
    "007": "HOSPITAL III EMERGENCIAS GRAU",
    "011": "POLICLINICO CHOSICA",
    "576": "POLICLINICO DE COMPLEJIDAD CRECIENTE SAN LUIS",
    "124": "POLICLINICO FRANCISCO PIZARRO",
    "029": "POSTA MEDICA CONSTRUCCION CIVIL"
}

if aten_file and resul_file and cartera_file:
    if st.button("🔍 Realizar búsqueda"):
        # Leer archivos
        df_aten = pd.read_csv(aten_file, sep="|", dtype=str)
        df_exam = pd.read_csv(resul_file, sep="|", dtype=str)
        df_cartera = pd.read_csv(cartera_file, sep="|", dtype=str)

        # Eliminar duplicados por DOC_PACIENTE
        df_aten_unique = df_aten.drop_duplicates(subset="DOC_PACIENTE", keep="first")

        # Filtrar exámenes clave
        codigos_requeridos = ["82043", "82565", "82570"]
        df_filtrado = df_exam[df_exam["EXAMEN"].isin(codigos_requeridos)]

        # Pacientes que tienen los 3 exámenes
        dni_con_tres = (
            df_filtrado.groupby("DNI")["EXAMEN"]
            .nunique()
            .reset_index()
            .query("EXAMEN == 3")["DNI"]
        )
        df_filtrado = df_filtrado[df_filtrado["DNI"].isin(dni_con_tres)]

        # Excluir si están en CarteraVisare
        dni_formateado = "1-" + df_filtrado["DNI"]
        df_filtrado = df_filtrado[~dni_formateado.isin(df_cartera["NUM-DOCMTO"])]

        # Merge con datos del paciente
        df_merge = df_filtrado.merge(df_aten_unique, left_on="DNI", right_on="DOC_PACIENTE", how="left")

        # Eliminar si la edad (ANNOS_y) está vacía
        df_merge = df_merge[df_merge["ANNOS_y"].notna()]

        # Mapear nombre del centro a IPRES
        df_merge["IPRES"] = df_merge["CENTRO_x"].map(ipres_dict).fillna("IPRES DESCONOCIDA")

        # Descripciones de exámenes actualizadas
        descripcion = {
            "82043": "DOSAJE DE ALBUMINA EN ORINA, MICROALBUMINA, CUANTITATIVA",
            "82565": "DOSAJE DE CREATININA EN SANGRE",
            "82570": "DOSAJE DE CREATININA; OTRA FUENTE (INCLUYE ORINA)"
        }
        df_merge["Descripción del examen"] = df_merge["EXAMEN"].map(descripcion)

        # Construcción del resultado
        df_resultado = df_merge[[
            "IPRES", "PERIODO_x", "DNI", "PACIENTE_x", "EXAMEN",
            "Descripción del examen", "ANNOS_y", "FECHA_CITA_x", "FECHA_RESULTADO"
        ]].rename(columns={
            "PERIODO_x": "PERIODO",
            "PACIENTE_x": "Nombre del paciente",
            "EXAMEN": "Código del examen",
            "ANNOS_y": "Edad",
            "FECHA_CITA_x": "Fecha de cita",
            "FECHA_RESULTADO": "Fecha de resultado"
        })

        # Ordenar por DNI ascendente
        df_resultado = df_resultado.sort_values(by="DNI")

        # Columnas en mayúsculas
        df_resultado.columns = df_resultado.columns.str.upper()

        # Mostrar en pantalla
        st.success(f"✅ Se encontraron {len(df_resultado)} registros válidos.")
        st.dataframe(df_resultado)

        # Obtener fecha y hora actual
        ahora = datetime.now().strftime("%Y%m%d_%H%M")

        # Funciones de exportación
        def to_txt(df):
            return df.to_csv(index=False, sep='|')

        def to_csv(df):
            return df.to_csv(index=False)

        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="RESULTADOS")
            return output.getvalue()

        # Botones de descarga con timestamp
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("⬇️ Descargar TXT", to_txt(df_resultado), file_name=f"resultado_{ahora}.txt", mime="text/plain")
        with col2:
            st.download_button("⬇️ Descargar CSV", to_csv(df_resultado), file_name=f"resultado_{ahora}.csv", mime="text/csv")
        with col3:
            st.download_button("⬇️ Descargar Excel", to_excel(df_resultado), file_name=f"resultado_{ahora}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
