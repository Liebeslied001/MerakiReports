import pandas as pd
import meraki
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(".env")

# Configuración
export_folder = 'EXPORTADOS'
output_file = os.path.join(export_folder, 'SwitchPorts.xlsx')

# Iniciar sesión en el dashboard de Meraki
dashboard = meraki.DashboardAPI(
    os.getenv("KEY"),
    output_log=False,
    suppress_logging=True
)

# Funciones para obtener datos
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

# Crear carpeta EXPORTADOS si no existe
if not os.path.exists(export_folder):
    os.makedirs(export_folder)

# Lista para almacenar los datos de los puertos
data = []
timespan = 2419200

# Iterar sobre cada organización
for org in tqdm(organizations, desc="Procesando organizaciones"):
    org_id = org['id']
    org_name = org.get('name', 'N/A')

    # Obtener redes de la organización
    networks = obtener_sedes(dashboard, org_id)
    network_mapping = {net['id']: net.get('name', 'N/A') for net in networks}

    # Obtener dispositivos de la organización
    try:
        devices = dashboard.organizations.getOrganizationDevices(org_id, total_pages='all')
    except Exception as e:
        print(f"Error al obtener dispositivos de la organización {org_id}: {e}")
        continue

    # Filtrar switches
    switches = [d for d in devices if d.get('productType') == 'switch']

    for device in switches:
        serial = device.get('serial')
        network_id = device.get('networkId')
        network_name = network_mapping.get(network_id, 'N/A')
        hostname = device.get('name', 'N/A')
        lanIP = device.get('lanIp', 'N/A')
        firmware = device.get('firmware', 'N/A')

        try:
            ports = dashboard.switch.getDeviceSwitchPortsStatuses(serial, timespan=timespan)
            ports_config = dashboard.switch.getDeviceSwitchPorts(serial)

            for port_config, port in zip(ports_config, ports):
                data.append({
                    "organizationName": org_name,
                    "organizationId": org_id,
                    "networkId": network_id,
                    "networkName": network_name,
                    "hostname": hostname,
                    "lanIP": lanIP,
                    "deviceFirmware": firmware,
                    "serial": serial,
                    "portId": port_config.get("portId"),
                    "name": port_config.get("name"),
                    "tags": ", ".join(port_config.get("tags", [])),
                    "enabled": port_config.get("enabled"),
                    "poeEnabled": port_config.get("poeEnabled"),
                    "type": port_config.get("type"),
                    "vlan": port_config.get("vlan"),
                    "voiceVlan": port_config.get("voiceVlan"),
                    "allowedVlans": port_config.get("allowedVlans"),
                    "isolationEnabled": port_config.get("isolationEnabled"),
                    "rstpEnabled": port_config.get("rstpEnabled"),
                    "stpGuard": port_config.get("stpGuard"),
                    "linkNegotiation": port_config.get("linkNegotiation"),
                    "linkNegotiationCapabilities": ", ".join(port_config.get("linkNegotiationCapabilities", [])),
                    "portScheduleId": port_config.get("portScheduleId"),
                    "udld": port_config.get("udld"),
                    "accessPolicyType": port_config.get("accessPolicyType"),
                    "accessPolicyNumber": port_config.get("accessPolicyNumber"),
                    "macAllowList": ", ".join(port_config.get("macAllowList", [])),
                    "stickyMacAllowList": ", ".join(port_config.get("stickyMacAllowList", [])),
                    "stickyMacAllowListLimit": port_config.get("stickyMacAllowListLimit"),
                    "stormControlEnabled": port_config.get("stormControlEnabled"),
                    "adaptivePolicyGroupId": port_config.get("adaptivePolicyGroupId"),
                    "adaptivePolicyGroup_id": port_config.get("adaptivePolicyGroup", {}).get("id"),
                    "adaptivePolicyGroup_name": port_config.get("adaptivePolicyGroup", {}).get("name"),
                    "peerSgtCapable": port_config.get("peerSgtCapable"),
                    "flexibleStackingEnabled": port_config.get("flexibleStackingEnabled"),
                    "daiTrusted": port_config.get("daiTrusted"),
                    "profile_enabled": port_config.get("profile", {}).get("enabled"),
                    "profile_id": port_config.get("profile", {}).get("id"),
                    "profile_iname": port_config.get("profile", {}).get("iname"),
                    "module_model": port_config.get("module", {}).get("model"),
                    "mirror_mode": port_config.get("mirror", {}).get("mode"),
                    "dot3az_enabled": port_config.get("dot3az", {}).get("enabled"),
                    "stackwiseVirtual_isStackWiseVirtualLink": port_config.get("stackwiseVirtual", {}).get("isStackWiseVirtualLink"),
                    "stackwiseVirtual_isDualActiveDetector": port_config.get("stackwiseVirtual", {}).get("isDualActiveDetector"),
                    "enabled_status": port.get("enabled"),
                    "status": port.get("status"),
                    "isUplink": port.get("isUplink"),
                    "errors": ", ".join(port.get("errors", [])),
                    "warnings": ", ".join(port.get("warnings", [])),
                    "speed": port.get("speed"),
                    "duplex": port.get("duplex"),
                    "securePort_enabled": port.get("securePort", {}).get("enabled"),
                    "securePort_active": port.get("securePort", {}).get("active"),
                    "authenticationStatus": port.get("securePort", {}).get("authenticationStatus"),
                    "spanningTree": ", ".join(port.get("spanningTree", {}).get("statuses", [])),
                    "poe_isAllocated": port.get("poe", {}).get("isAllocated"),
                    "usage_total_kb": port.get("usageInKb", {}).get("total"),
                    "usage_sent_kb": port.get("usageInKb", {}).get("sent"),
                    "usage_recv_kb": port.get("usageInKb", {}).get("recv"),
                    "clientCount": port.get("clientCount"),
                    "powerUsageInWh": port.get("powerUsageInWh"),
                    "traffic_total_kbps": port.get("trafficInKbps", {}).get("total"),
                    "traffic_sent_kbps": port.get("trafficInKbps", {}).get("sent"),
                    "traffic_recv_kbps": port.get("trafficInKbps", {}).get("recv"),
                    "cdp_systemName": port.get("cdp", {}).get("systemName"),
                    "cdp_platform": port.get("cdp", {}).get("platform"),
                    "cdp_deviceId": port.get("cdp", {}).get("deviceId"),
                    "cdp_portId": port.get("cdp", {}).get("portId"),
                    "cdp_nativeVlan": port.get("cdp", {}).get("nativeVlan"),
                    "cdp_address": port.get("cdp", {}).get("address"),
                    "cdp_managementAddress": port.get("cdp", {}).get("managementAddress"),
                    "cdp_version": port.get("cdp", {}).get("version"),
                    "cdp_vtpManagementDomain": port.get("cdp", {}).get("vtpManagementDomain"),
                    "cdp_capabilities": port.get("cdp", {}).get("capabilities"),
                    "lldp_systemName": port.get("lldp", {}).get("systemName"),
                    "lldp_systemDescription": port.get("lldp", {}).get("systemDescription"),
                    "lldp_chassisId": port.get("lldp", {}).get("chassisId"),
                    "lldp_portId": port.get("lldp", {}).get("portId"),
                    "lldp_managementVlan": port.get("lldp", {}).get("managementVlan"),
                    "lldp_portVlan": port.get("lldp", {}).get("portVlan"),
                    "lldp_managementAddress": port.get("lldp", {}).get("managementAddress"),
                    "lldp_portDescription": port.get("lldp", {}).get("portDescription"),
                    "lldp_systemCapabilities": port.get("lldp", {}).get("systemCapabilities"),
                })

        except Exception as e:
            print(f"Error obteniendo puertos para {serial}: {e}")

# Exportar a Excel
ports_df = pd.DataFrame(data)
ports_df.to_excel(output_file, index=False)

print(f"Información de puertos exportada a {output_file}")
