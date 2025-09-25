# Diafaan Monitoring Scripts

Colección de scripts en **Python** para monitorear sistemas de mensajería **Diafaan**, VoIP y SMPP mediante **Nagios** y visualización en **Grafana**.

## 🛠️ Funcionalidades
- Verificación de latencia TCP hacia gateways.
- Cálculo de TPS (transacciones por segundo).
- Monitoreo de colas (`SendQueue`).
- Validación de errores en gateways específicos.
- Control de prioridades de mensajes.
- Exportación de métricas compatibles con Nagios/PNP4Nagios.

## 📂 Scripts incluidos
- `latencia_GW.py`: mide latencia TCP/IP de gateways.
- `GW_status.py`: valida si una gateway está activa via XML API.
- `GW_TPS.py`: calcula TPS de un gateway.
- `Total_TPS.py`: TPS global del sistema.
- `TotalSMS.py`: cuenta total de SMS en base de datos.
- `Q_completo.py`: verifica colas activas.
- `SendQueue.py`: mide mensajes pendientes en la cola.
- `total_Priority.py`: analiza mensajes por prioridad.
- `Total_SMS_priority.py`: combinaciones de prioridades.
- ... (y más scripts agregados según necesidades).

## 🚨 Integración con Nagios
Cada script retorna códigos de salida estándar:
- `0` = OK
- `1` = WARNING
- `2` = CRITICAL
- `3` = UNKNOWN

Ejemplo de uso:
```bash
python latencia_GW.py 192.168.1.10 5060
