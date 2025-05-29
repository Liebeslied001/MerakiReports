import meraki
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv(".env")

# Inicializar API Meraki
dashboard = meraki.DashboardAPI(
    os.getenv("KEY"),
    output_log=False,
    suppress_logging=True
)

# Definir carpeta raíz de exportación
EXPORT_FOLDER = "ReportesDiarios"

# Crear carpeta raíz si no existe
os.makedirs(EXPORT_FOLDER, exist_ok=True)

# Obtener todas las organizaciones
try:
    organizations = dashboard.organizations.getOrganizations()
except Exception as e:
    print(f"Error al obtener organizaciones: {e}")
    organizations = []

# Iterar sobre cada organización
for org in organizations:
    org_id = org['id']
    org_name = org['name'].replace("/", "-")  # Evitar caracteres no válidos en nombres de carpetas

    # Crear carpeta de la organización
    org_folder = os.path.join(EXPORT_FOLDER, org_name)
    os.makedirs(org_folder, exist_ok=True)

    print(f"Procesando organización: {org_name}")

    try:
        networks = dashboard.organizations.getOrganizationNetworks(org_id, total_pages='all')
    except Exception as e:
        print(f"Error al obtener redes de la organización {org_name}: {e}")
        networks = []

    # Iterar sobre cada red
    for net in networks:
        net_id = net['id']
        net_name = net['name'].replace("/", "-")  # Evitar caracteres no válidos

        # Crear carpeta de la red
        net_folder = os.path.join(org_folder, net_name)
        os.makedirs(net_folder, exist_ok=True)

        print(f"  Procesando red: {net_name}")

        # Obtener clientes de la red (últimas 24 horas, por ejemplo)
        try:
            clients = dashboard.networks.getNetworkClients(
                net_id,
                total_pages='all',
                timespan=86400  # 24 horas
            )
        except Exception as e:
            print(f"    Error al obtener clientes de la red {net_name}: {e}")
            clients = []

        # Crear DataFrame
        df = pd.DataFrame(clients)

        # Generar nombre de archivo con fecha y hora
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"clientes_{fecha_actual}.xlsx"
        filepath = os.path.join(net_folder, filename)

        # Exportar a Excel
        df.to_excel(filepath, index=False)
        print(f"    Clientes exportados a: {filepath}")

print("\n✅ Exportación finalizada. Archivos generados en la carpeta ReportesDiarios.")