FROM ubuntu:latest
LABEL authors="Cristian"
# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos y el código de la aplicación
COPY requirements.txt .
COPY proyecto.py .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto donde se ejecutará la aplicación
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "proyecto.py"]

ENTRYPOINT ["top", "-b"]