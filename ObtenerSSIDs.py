import meraki
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv(".env")

dashboard = meraki.DashboardAPI(
    os.getenv("KEY"),
    output_log=False,
    suppress_logging=True
)

def obtener_organizaciones(dashboard):
    """Obtiene todas las organizaciones disponibles en el dashboard."""
    try:
        return dashboard.organizations.getOrganizations()
    except Exception as e:
        print(f"Error al obtener organizaciones: {e}")
        return []

def obtener_sedes(dashboard, organization_id):
    """Obtiene todas las redes de una organización específica."""
    try:
        return dashboard.organizations.getOrganizationNetworks(organization_id, total_pages='all')
    except Exception as e:
        print(f"Error al obtener redes de la organización {organization_id}: {e}")
        return []

def obtener_ssids(dashboard, network_id):
    """Obtiene todos los SSIDs de una red específica."""
    try:
        return dashboard.wireless.getNetworkWirelessSsids(network_id)
    except Exception as e:
        print(f"Error al obtener SSIDs de la red {network_id}: {e}")
        return []

def procesar_datos_ssid(org, network, ssid):
    """Procesa los datos de un SSID y devuelve un diccionario con la información."""
    return {
        'Organization ID': org['id'],
        'Organization Name': org['name'],
        'Network ID': network['id'],
        'Network Name': network['name'],
        'SSID Number': ssid.get('number'),
        'SSID Name': ssid.get('name'),
        'Enabled': ssid.get('enabled'),
        'Splash Page': ssid.get('splashPage'),
        'SSID Admin Accessible': ssid.get('ssidAdminAccessible'),
        'Local Auth': ssid.get('localAuth'),
        'Auth Mode': ssid.get('authMode'),
        'Encryption Mode': ssid.get('encryptionMode'),
        'WPA Encryption Mode': ssid.get('wpaEncryptionMode'),
        'Psk': ssid.get('psk'),
        'Radius Enabled': ssid.get('radiusEnabled'),
        'Radius Servers': str(ssid.get('radiusServers', [])),
        'Radius Accounting Enabled': ssid.get('radiusAccountingEnabled'),
        'IP Assignment Mode': ssid.get('ipAssignmentMode'),
        'Use VLAN Tagging': ssid.get('useVlanTagging'),
        'Default VLAN ID': ssid.get('defaultVlanId'),
        'Radius Override': ssid.get('radiusOverride'),
        'Min Bitrate': ssid.get('minBitrate'),
        'Band Selection': ssid.get('bandSelection'),
        'Per Client Bandwidth Limit Up': ssid.get('perClientBandwidthLimitUp'),
        'Per Client Bandwidth Limit Down': ssid.get('perClientBandwidthLimitDown'),
        'Per SSID Bandwidth Limit Up': ssid.get('perSsidBandwidthLimitUp'),
        'Per SSID Bandwidth Limit Down': ssid.get('perSsidBandwidthLimitDown'),
        'Mandatory DHCP Enabled': ssid.get('mandatoryDhcpEnabled'),
        'LAN Isolation Enabled': ssid.get('lanIsolationEnabled'),
        'Visible': ssid.get('visible'),
        'Available On All APs': ssid.get('availableOnAllAps'),
        'Availability Tags': ', '.join(ssid.get('availabilityTags', [])),
    }

def generar_reporte_ssids(dashboard):
    """Función principal para generar el reporte de SSIDs."""
    data = []
    organizaciones = obtener_organizaciones(dashboard)

    for organizacion in organizaciones:
        sedes = obtener_sedes(dashboard, organizacion['id'])
        for sede in sedes:
            ssids = obtener_ssids(dashboard, sede['id'])
            for ssid in ssids:
                try:
                    fila = procesar_datos_ssid(organizacion, sede, ssid)
                    data.append(fila)
                except Exception as e:
                    print(f"Error al procesar SSID: {e}")
    return pd.DataFrame(data)

def guardar_reporte(df, filename='SSIDs.xlsx'):
    """Guarda el DataFrame en un archivo Excel en la carpeta EXPORTADOS."""
    try:
        export_folder = "EXPORTADOS"
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)

        output_path = os.path.join(export_folder, filename)
        df.to_excel(output_path, index=False)
        print(f'Reporte generado: {output_path}')
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")

if __name__ == "__main__":
    df_resultado = generar_reporte_ssids(dashboard)
    guardar_reporte(df_resultado)
