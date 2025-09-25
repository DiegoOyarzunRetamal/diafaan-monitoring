# -*- coding: utf-8 -*-
"""
Script: latencia_GW.py
Autor: Diego Oyarzun Retamal
Fecha de creación: 2024-09-25
Versión: 1.0
Descripción:
    Mide la latencia TCP hacia una IP y puerto específico.
    Integra con Nagios y retorna códigos de estado estándar:
        0 = OK, 1 = WARNING, 2 = CRITICAL
    También exporta datos de rendimiento compatibles con PNP4Nagios.

Uso:
    python latencia_GW.py <IP> <Puerto>

Ejemplo:
    python latencia_GW.py 192.168.1.10 5060

Dependencias:
    - Python 3.x
    (solo librerías estándar: socket, time, argparse, sys)
"""

import socket
import time
import argparse
import sys


def medir_latencia(ip, puerto):
    """
    Intenta establecer una conexión TCP a la IP y puerto especificados.
    Devuelve la latencia en ms o un error si no se puede conectar.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # Tiempo máximo de espera = 5 segundos
    
    try:
        inicio = time.time()
        sock.connect((ip, puerto))
        fin = time.time()

        latencia = (fin - inicio) * 1000  # milisegundos
        sock.close()

        return latencia, None
    except socket.timeout:
        return None, "Tiempo de espera agotado. No se pudo conectar."
    except socket.error as e:
        return None, f"Error de conexión: {e}"


def main():
    parser = argparse.ArgumentParser(description="Medir la latencia de una IP y puerto mediante TCP.")
    parser.add_argument("ip", help="Dirección IP del servidor de destino")
    parser.add_argument("puerto", type=int, help="Número de puerto del servidor de destino")
    args = parser.parse_args()

    latencia, error = medir_latencia(args.ip, args.puerto)
    
    if error:
        print(f"CRITICAL: {error} | latencia=0ms")
        sys.exit(2)  # CRITICAL
    elif latencia > 1000:
        print(f"WARNING: Latencia hacia {args.ip}:{args.puerto} = {latencia:.2f} ms | latencia={latencia:.2f}ms")
        sys.exit(1)  # WARNING
    else:
        print(f"OK: Latencia hacia {args.ip}:{args.puerto} = {latencia:.2f} ms | latencia={latencia:.2f}ms")
        sys.exit(0)  # OK


if __name__ == "__main__":
    main()
