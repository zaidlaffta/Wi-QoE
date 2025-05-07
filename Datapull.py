import meraki
import time
import csv
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = 'YOUR_API_KEY'
NETWORK_ID = 'YOUR_NETWORK_ID'
ORG_ID = 'YOUR_ORG_ID'
INTERVAL = 30  # Polling interval in seconds

dashboard = meraki.DashboardAPI(api_key=API_KEY, suppress_logging=True)

# Output CSV setup
filename = f"meraki_full_telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
        'timestamp', 'client_mac', 'description', 'ip', 'ssid', 'status', 'rssi',
        'usage_up', 'usage_down', 'manufacturer', 'recent_device_mac',
        'assoc_duration', 'auth_fails', 'dns_latency_avg', 'dhcp_latency_avg',
        'roaming_count', 'retry_count', 'packet_loss_percent', 'latency_avg',
        'uplink_bandwidth_class'
    ])

# --- POLLING LOOP ---
while True:
    try:
        timestamp = datetime.now().isoformat()
        clients = dashboard.networks.getNetworkClients(networkId=NETWORK_ID, perPage=100)

        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            for client in clients:
                mac = client.get('mac')
                client_id = client.get('id')
                device_serial = client.get('recentDeviceSerial')

                # Wireless connection stats
                stats = dashboard.networks.getNetworkWirelessClientConnectionStats(NETWORK_ID, mac)
                assoc = stats.get('association', {})
                dhcp = stats.get('dhcp', {})
                dns = stats.get('dns', {})
                roams = stats.get('roaming', {})
                latency = stats.get('latency', {})

                writer.writerow([
                    timestamp,
                    mac,
                    client.get('description', ''),
                    client.get('ip', ''),
                    client.get('ssid', ''),
                    client.get('status', ''),
                    client.get('rssi', ''),
                    client.get('usage', {}).get('sent', ''),
                    client.get('usage', {}).get('recv', ''),
                    client.get('manufacturer', ''),
                    client.get('recentDeviceMac', ''),
                    assoc.get('duration', ''),
                    assoc.get('authFails', ''),
                    dns.get('avg', ''),
                    dhcp.get('avg', ''),
                    roams.get('numRoams', ''),
                    assoc.get('retryCount', ''),
                    assoc.get('packetLossPercent', ''),
                    latency.get('avg', ''),
                    client.get('uplink', {}).get('bandwidthLimit', {}).get('limitUp', '')
                ])
        print(f"[{timestamp}] Logged data for {len(clients)} clients.")
        time.sleep(INTERVAL)

    except Exception as e:
        print("Error:", e)
        time.sleep(INTERVAL)
