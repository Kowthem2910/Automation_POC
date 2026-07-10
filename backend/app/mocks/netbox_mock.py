"""
Mock NetBox API.

REAL FLOW NOTE: production calls NetBox's REST API
(`/api/dcim/devices/`, `/api/virtualization/virtual-machines/`) to resolve
CI ownership and metadata referenced during ticket enrichment.
"""

CIS = {
    "web01.prod.internal": {
        "name": "web01.prod.internal",
        "role": "Web Server",
        "site": "East Data Center",
        "owner": "Platform Engineering",
        "status": "Active",
    },
    "vpn-gw-east-01": {
        "name": "vpn-gw-east-01",
        "role": "VPN Gateway",
        "site": "East Data Center",
        "owner": "Network Ops",
        "status": "Active",
    },
}


def get_ci(name: str):
    """Mirrors: GET /netbox/api/dcim/devices/?name={name}"""
    return CIS.get(name)
