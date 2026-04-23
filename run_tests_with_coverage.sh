#!/usr/bin/env bash
# Script para ejecutar pruebas con cobertura para SonarQube

# Activar entorno virtual
source ../.venv/Scripts/activate

# Instalar coverage si no está
pip install coverage

# Ejecutar pruebas con cobertura
coverage run -m unittest discover -s tests
coverage xml

echo "Cobertura generada en coverage.xml"