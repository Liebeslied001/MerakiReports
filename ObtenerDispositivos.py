import meraki
import pandas as pd
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(".env")

dashboard = meraki.DashboardAPI(
    os.getenv("KEY"),
    output_log=False,
    suppress_logging=True
)

def obtener_organizaciones(dashboard):
    try:
        return dashboard.organizations.getOrganizations()
    except Exception as e:
        print(f"Error al obtener organizaciones: {e}")
        return []

def obtener_sedes(dashboard, organization_id):
    try:
        return dashboard.organizations.getOrganizationNetworks(organization_id, total_pages='all')
    except Exception as e:
        print(f"Error al obtener redes de la organización {organization_id}: {e}")
        return []

# Obtener todas las organizaciones
organizations = obtener_organizaciones(dashboard)

# Lista para almacenar los datos de los dispositivos
devices_data = []

# Iterar sobre cada organización
for org in tqdm(organizations, desc="Procesando organizaciones"):
    org_id = org['id']

    # Obtener redes de la organización
    networks = obtener_sedes(dashboard, org_id)
    network_mapping = {network['id']: network['name'] for network in networks}

    # Obtener dispositivos de la organización
    try:
        devices = dashboard.organizations.getOrganizationDevices(org_id, total_pages='all')
    except Exception as e:
        print(f"Error al obtener dispositivos de la organización {org_id}: {e}")
        continue

    for device in devices:
        serial = device.get("serial", "N/A")

        device_info = {
            "organizationId": org_id,
            "organizationName": org['name'],
            "networkId": device.get("networkId", "N/A"),
            "networkName": network_mapping.get(device.get("networkId"), "Unknown"),
            "name": device.get("name", "N/A"),
            "lat": device.get("lat", "N/A"),
            "lng": device.get("lng", "N/A"),
            "address": device.get("address", "N/A"),
            "notes": device.get("notes", "N/A"),
            "tags": ", ".join(device.get("tags", [])),
            "serial": serial,
            "model": device.get("model", "N/A"),
            "mac": device.get("mac", "N/A"),
            "lanIp": device.get("lanIp", "N/A"),
            "firmware": device.get("firmware", "N/A"),
            "productType": device.get("productType", "N/A"),
        }

        # Agregar detalles adicionales si existen
        details = device.get("details", [])
        for detail in details:
            key = detail.get("name")
            if key and key.lower() != "monitoring version":
                device_info[key] = detail.get("value", "N/A")

        # Configuración de radio si es wireless
        if serial and device.get("productType") == "wireless":
            try:
                radio_settings = dashboard.wireless.getDeviceWirelessRadioSettings(serial)
                twoGhz = radio_settings.get("twoFourGhzSettings", {})
                fiveGhz = radio_settings.get("fiveGhzSettings", {})

                device_info["rfProfileId"] = radio_settings.get("rfProfileId", "N/A")
                device_info["2.4GHz Channel"] = twoGhz.get("channel", "N/A")
                device_info["2.4GHz Target Power"] = twoGhz.get("targetPower", "N/A")
                device_info["5GHz Channel"] = fiveGhz.get("channel", "N/A")
                device_info["5GHz Channel Width"] = fiveGhz.get("channelWidth", "N/A")
                device_info["5GHz Target Power"] = fiveGhz.get("targetPower", "N/A")
            except Exception as e:
                print(f"Error al obtener radio settings para {serial}: {e}")

        # Obtener configuración de interfaz de gestión
        try:
            mgmt = dashboard.devices.getDeviceManagementInterface(serial)

            # WAN1
            wan1 = mgmt.get("wan1", {})
            device_info["wan1_using_static_ip"] = wan1.get("usingStaticIp", "N/A")
            device_info["wan1_static_ip"] = wan1.get("staticIp", "N/A")
            device_info["wan1_subnet"] = wan1.get("staticSubnetMask", "N/A")
            device_info["wan1_gateway"] = wan1.get("staticGatewayIp", "N/A")
            device_info["wan1_dns"] = ", ".join(wan1.get("staticDns", []))
            device_info["wan1_vlan"] = wan1.get("vlan", "N/A")

        except Exception as e:
            print(f"Error al obtener interfaz de gestión para {serial}: {e}")

        devices_data.append(device_info)

# Crear DataFrame
df = pd.DataFrame(devices_data)

# Reordenar columnas principales al principio
column_order = [
    "organizationId", "organizationName", "networkId", "networkName",
    "name", "model", "serial", "mac", "lanIp", "address", "notes", "tags",
    "firmware", "productType", "lat", "lng",
    "rfProfileId", "2.4GHz Channel", "2.4GHz Target Power",
    "5GHz Channel", "5GHz Channel Width", "5GHz Target Power",
    "wan1_using_static_ip", "wan1_static_ip", "wan1_subnet", "wan1_gateway", "wan1_dns", "wan1_vlan"
]

df = df.reindex(columns=[col for col in column_order if col in df.columns] + [col for col in df.columns if col not in column_order])

# Crear carpeta "EXPORTADOS" si no existe
export_folder = "EXPORTADOS"
if not os.path.exists(export_folder):
    os.makedirs(export_folder)

# Guardar archivo en la carpeta "EXPORTADOS"
output_file = os.path.join(export_folder, "Dispositivos.xlsx")
df.to_excel(output_file, index=False)

print(f"Los resultados se han exportado a '{output_file}'.")
