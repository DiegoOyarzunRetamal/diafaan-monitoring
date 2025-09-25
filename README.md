# Diafaan Monitoring & Alerting Scripts

Colección de scripts en **Python** desarrollados para implementar un sistema de monitoreo y alertas de **VoIP** y **SMPP**, integrando **Nagios** y **Grafana**.  
Estos scripts permiten supervisar en tiempo real el estado de **gateways**, **colas de envío**, **TPS (transactions per second)**, **latencia** y **errores críticos** en servidores basados en **Diafaan**.

## 🚀 Objetivo
Reducir los tiempos de respuesta ante incidentes críticos (MTTR), asegurando la continuidad de servicios de mensajería y VoIP.  
Este sistema fue utilizado en producción y posteriormente publicado aquí como muestra de experiencia profesional.

---

## 📂 Scripts incluidos

### 🔧 Verificación de conectividad y latencia
- **`latencia_GW.py`**  
  Mide la latencia hacia una IP y puerto TCP específicos. Retorna códigos Nagios (`OK`, `WARNING`, `CRITICAL`).

### 📈 Cálculo de TPS (Transactions Per Second)
- **`GW_TPS.py`**  
  Calcula el TPS de un **gateway específico** en SQL Server, usando credenciales desde `Setting.ini`.  
- **`Total_TPS.py`**  
  Calcula el TPS total del sistema en SQL Server.  
- **`total_tpsconn.py`** *(prototipo)*  
  Calcula el TPS en SQLite para múltiples `ConnectorId`.

### 🛰️ Estado de gateways
- **`GW_status.py`**  
  Consulta el XML de estado y verifica si una **gateway está activa**.  
- **`GW_errors.py`**  
  Verifica cantidad de errores (`StatusCode`) por gateway en la base SQLite.  
- **`Q_completo.py`**  
  Consulta cuántos mensajes hay en la cola `SendQueue` para gateways activos definidos.

### 📨 Monitoreo de colas y prioridades
- **`SendQueue.py`**  
  Verifica cuántos mensajes hay pendientes en la cola `SendQueue` de un gateway.  
- **`TotalSMS.py`**  
  Cuenta cuántos SMS totales hay en la base de datos SQL Server.  
- **`Total_priority.py`**  
  Valida mensajes pendientes por **una prioridad** específica.  
- **`Total_SMS_priority.py`**  
  Valida mensajes pendientes para **múltiples prioridades** en simultáneo.

### 📊 Métricas específicas de Diafaan
- **`MessagesInSendQueue.py`**  
  Consume la API XML de Diafaan para obtener el valor de `MessagesInSendQueue`.  
- **`TotalRecords.py`**  
  Cuenta registros en `MessageLog` en SQL Server mediante `sqlcmd`.

---

## ⚙️ Uso de los scripts

Ejemplo 1: medir latencia a un gateway SIP en el puerto 5060
```bash
python latencia_GW.py 192.168.1.10 5060
Ejemplo 2: verificar TPS de un gateway

bash
Copiar código
python GW_TPS.py Gateway_SMPP_1
Ejemplo 3: comprobar mensajes en la cola de prioridad 1

bash
Copiar código
python Total_priority.py 1
Todos los scripts retornan:

0 → OK

1 → WARNING

2 → CRITICAL

3 → UNKNOWN

Esto los hace compatibles con Nagios / PNP4Nagios.

🖥️ Dependencias
Los scripts requieren:

Python 3.x

Librerías externas:

bash
Copiar código
pip install pyodbc requests
Además, dependen de:

Archivo de configuración: Setting.ini

Archivo de licencia: License.py (para fecha de expiración)

📊 Integración con Nagios
Ejemplo de definición de comando:

cfg
Copiar código
define command{
    command_name    check_latencia_gw
    command_line    /usr/bin/python3 /opt/nagios/checks/latencia_GW.py $ARG1$ $ARG2$
}
Ejemplo de servicio:

cfg
Copiar código
define service{
    use                     generic-service
    host_name               smpp-gateway
    service_description     Latencia SMPP Gateway
    check_command           check_latencia_gw!192.168.1.10!2775
}
📈 Integración con Grafana y Prometheus
Los scripts pueden exponerse como exporters vía prometheus_client en Python.

Métricas recomendadas:

tps_gateway

messages_in_queue

gateway_status

errors_per_gateway

Con Prometheus recolectando estas métricas, Grafana permite construir dashboards con:

Latencia por gateway

TPS global y por gateway

Colas pendientes

Tasa de errores
