# -*- coding: utf-8 -*-
#"""
#Script: GW_status_email.py
#Autor: Diego Oyarzun Retamal 
#Fecha de creación: 2025-09-25
#Versión: 1.0
#Descripción:
#    Verifica el estado de un Gateway en Diafaan a través de su API XML.
#    Integra con Nagios y envía alertas por correo electrónico cuando 
#    se detectan cambios de estado (caída o recuperación).
#    Además registra eventos en un log y guarda el estado previo en un archivo.
#
#Uso:
#    python GW_status_email.py <GatewayName>
#
#Ejemplo:
#    python GW_status_email.py SMPP_Gateway_1
#
#Dependencias:
#    - Python 3.x
#    - requests
#    - smtplib (incluido en librería estándar)
#
#Archivos requeridos:
#    - Setting.ini   → contiene la URL del XML
#    - License.py    → contiene función get_expiration_date()
#    - gateway_status.txt → almacena el estado previo de gateways
#    - gateway_events.log → registra los eventos con timestamp
#
#Nota de seguridad:
#    ⚠️ Reemplazar credenciales de correo por valores configurables en 
#    variables de entorno o Setting.ini. Nunca exponer datos sensibles 
#    en repositorios públicos.
#"""

import requests
import xml.etree.ElementTree as ET
import sys
import configparser
import datetime
import importlib.util
import os
import smtplib
from email.mime.text import MIMEText

# Estados Nagios
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

# Rutas (ajustar según entorno)
setting_config_path = r'C:\T-Voip\Monitor\OTP\Setting.ini'
license_config_path = r'C:\T-Voip\Monitor\OTP\License.py'
status_file_path = r'C:\T-Voip\Monitor\OTP\gateway_status.txt'
log_file_path = r'C:\T-Voip\Monitor\OTP\gateway_events.log'

# Leer configuración
setting_config = configparser.ConfigParser()
setting_config.read(setting_config_path)

if 'URL' in setting_config and 'url' in setting_config['URL']:
    url = setting_config.get('URL', 'url')
else:
    print("Error: La sección o clave URL no se encontró en Setting.ini")
    sys.exit(STATE_UNKNOWN)

# Verificar licencia
spec = importlib.util.spec_from_file_location("license_config", license_config_path)
license_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(license_config)

try:
    expiration_date_str = license_config.get_expiration_date()
    expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    if datetime.date.today() > expiration_date:
        print("CRITICAL: El script ha caducado.")
        sys.exit(STATE_CRITICAL)
except AttributeError:
    print("Error: No se encontró la fecha de expiración en License.py")
    sys.exit(STATE_UNKNOWN)

# Registrar evento en log
def log_event(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

# Enviar correo con SMTP_SSL
def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "T-Voip Alerta <alerta@t-voip.com>"
    msg['To'] = "soporte@t-voip.com"

    try:
        server = smtplib.SMTP_SSL("t-voip.com", 465)
        # ⚠️ Reemplazar por credenciales seguras en producción
        server.login("alerta@t-voip.com", "password_aqui")
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
        server.quit()
    except Exception as e:
        log_event(f"ERROR al enviar correo: {e}")
        print(f"UNKNOWN: No se pudo enviar el correo: {e}")
        sys.exit(STATE_UNKNOWN)

# Verificar estado de gateway
def check_gateway_status(url, gateway_name):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        for gateway in root.findall('.//Gateway'):
            name = gateway.get('Name')
            if name == gateway_name:
                active = gateway.get('Active')
                update_status(gateway_name, active == '1', gateway, root)
                if active == '1':
                    print(f'OK: La gateway "{gateway_name}" está activa. | gateway_status=1')
                    return STATE_OK
                else:
                    print(f'WARNING: La gateway "{gateway_name}" no está activa. | gateway_status=0')
                    return STATE_WARNING

        print(f'CRITICAL: No se encontró la gateway con el nombre "{gateway_name}". | gateway_status=0')
        return STATE_CRITICAL

    except requests.RequestException as e:
        log_event(f"ERROR de conexión al obtener XML: {e}")
        print(f'UNKNOWN: Error al obtener el XML: {e} | gateway_status=0')
        return STATE_UNKNOWN
    except ET.ParseError as e:
        log_event(f"ERROR al analizar XML: {e}")
        print(f'UNKNOWN: Error al analizar el XML: {e} | gateway_status=0')
        return STATE_UNKNOWN

# Leer/actualizar estado y registrar cambios
def update_status(gateway_name, is_active, gateway_data, xml_root):
    status = {}

    # Leer estado anterior
    if os.path.exists(status_file_path):
        with open(status_file_path, 'r') as f:
            for line in f:
                name, value = line.strip().split('=')
                status[name] = value == 'active'

    prev_state = status.get(gateway_name, True)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Extraer datos del XML de la sección Gateway
    status_text = gateway_data.findtext('Status', default='N/A')
    statistics = gateway_data.find('Statistics')
    sent = statistics.findtext('SentMessages', default='0') if statistics is not None else '0'
    failed = statistics.findtext('FailedMessages', default='0') if statistics is not None else '0'
    received = statistics
