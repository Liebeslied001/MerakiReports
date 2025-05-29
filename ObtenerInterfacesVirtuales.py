import meraki
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv(".env")

# Inicializar el cliente del dashboard
dashboard = meraki.DashboardAPI(
    os.getenv("KEY"),
    output_log=False,  # Desactiva los logs en consola
    suppress_logging=True  # Suprime el logging
)

# Obtener todas las organizaciones
organizations = dashboard.organizations.getOrganizations()

# Definir la carpeta de salida y el nombre del archivo
output_folder = "EXPORTADOS"
output_file = os.path.join(output_folder, "InterfacesVirtuales.xlsx")

# Crear la carpeta si no existe
os.makedirs(output_folder, exist_ok=True)

# Lista para almacenar los datos
data = []

try:
    for org in organizations:
        organization_id = org['id']
        
        # Obtener todas las redes de la organización
        networks = dashboard.organizations.getOrganizationNetworks(organization_id, total_pages='all')
        
        for network in networks:
            # Obtener las pilas de switches
            try:
                sw_stacks = dashboard.switch.getNetworkSwitchStacks(network['id'])
                for sw_stack in sw_stacks:
                    try:
                        routing_interfaces = dashboard.switch.getNetworkSwitchStackRoutingInterfaces(
                            network['id'], sw_stack['id']
                        )
                        
                        if not routing_interfaces:
                            print(f"No se hallaron interfaces en el stack con identificador: {sw_stack['id']}")
                        
                        for interface in routing_interfaces:
                            dhcp_info = dashboard.switch.getNetworkSwitchStackRoutingInterfaceDhcp(
                                network['id'], sw_stack['id'], interface.get('interfaceId')
                            )
                            
                            data.append([
                                org['name'], organization_id, network['name'], network['id'], sw_stack['name'], sw_stack['id'],
                                interface.get('interfaceId'), interface.get('vlanId'), interface.get('name'),
                                interface.get('subnet'), interface.get('interfaceIp'), None,  # No aplica serial
                                dhcp_info.get('dhcpMode'), dhcp_info.get('dnsNameserversOption'),
                                ', '.join(dhcp_info.get('dnsCustomNameservers', [])), 
                                ', '.join([f"{r['start']} - {r['end']} ({r['comment']})" for r in dhcp_info.get('reservedIpRanges', [])]),
                                ', '.join([f"{a['name']} ({a['mac']}) -> {a['ip']}" for a in dhcp_info.get('fixedIpAssignments', [])])
                            ])
                    except Exception as e:
                        print(f"Error al obtener interfaces para el stack {sw_stack['id']} en la red {network['id']}: {e}")
            except Exception as e:
                print(f"Error al obtener las pilas de switches para la red {network['id']}: {e}")
            
            # Obtener dispositivos de la red
            try:
                devices = dashboard.networks.getNetworkDevices(network['id'])
                for device in devices:
                    if 'MS' in device.get('model', ''):
                        try:
                            routing_interfaces = dashboard.switch.getDeviceSwitchRoutingInterfaces(device['serial'])
                            
                            if not routing_interfaces:
                                print(f"No se hallaron interfaces en el switch con numero de serie: {device['serial']}")
                            
                            for interface in routing_interfaces:
                                dhcp_info = dashboard.switch.getDeviceSwitchRoutingInterfaceDhcp(
                                    device['serial'], interface.get('interfaceId')
                                )
                                
                                data.append([
                                    org['name'], organization_id, network['name'], network['id'], device['name'], None,  # No aplica StackID
                                    interface.get('interfaceId'), interface.get('vlanId'), interface.get('name'),
                                    interface.get('subnet'), interface.get('interfaceIp'), device['serial'],
                                    dhcp_info.get('dhcpMode'), dhcp_info.get('dnsNameserversOption'),
                                    ', '.join(dhcp_info.get('dnsCustomNameservers', [])),
                                    ', '.join([f"{r['start']} - {r['end']} ({r['comment']})" for r in dhcp_info.get('reservedIpRanges', [])]),
                                    ', '.join([f"{a['name']} ({a['mac']}) -> {a['ip']}" for a in dhcp_info.get('fixedIpAssignments', [])])
                                ])
                        except Exception as e:
                            if "not supported for switches in switch stack" in str(e):
                                print(f"Omitiendo switch {device['serial']} en la red {network['id']} porque está en un stack.")
                            else:
                                print(f"Error al obtener interfaces del switch {device['serial']} en la red {network['id']}: {e}")
            except Exception as e:
                print(f"Error al obtener los dispositivos de la red {network['id']}: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")

# Crear un DataFrame y exportar a Excel
df = pd.DataFrame(data, columns=[
    "Organization", "OrganizationID", "Network", "NetworkID", "Switch o SwitchStack", "SwitchStackID", 
    "InterfaceID", "VLAN", "Name", "Subnet", "IP", "SwitchSerialNumber", "dhcpMode", 
    "dnsNameserversOption", "dnsCustomNameservers", "ReservedIpRanges", "FixedIpAssignments"
])

try:
    df.to_excel(output_file, index=False)
    print(f"Todas las interfaces virtuales se han exportado a {output_file} con éxito.")
except Exception as e:
    print(f"Error al guardar el archivo Excel: {e}")
