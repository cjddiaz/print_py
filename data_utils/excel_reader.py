import pandas as pd

class ExcelReader:
    @staticmethod
    def load_excel(file_path: str):
        """
        Lee un archivo excel y devuelve una lista de diccionarios con los datos y el listado de columnas.
        Ej: [{"ColA": "Dato1", "ColB": "Dato2"}, ...]
        """
        try:
            df = pd.read_excel(file_path)
            # Normalizar NaNs
            df = df.fillna("")
            records = df.to_dict(orient='records')
            columns = df.columns.tolist()
            return records, columns
        except Exception as e:
            raise Exception(f"Error al leer el archivo Excel: {e}")
