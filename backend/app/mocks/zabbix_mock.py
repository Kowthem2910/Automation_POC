"""
Mock Zabbix API.

REAL FLOW NOTE: production calls Zabbix's JSON-RPC API (`alert.get` /
`problem.get`) filtered by host group / severity. This mock returns a
static active-alert fixture so the router can demonstrate correlating a
user's report to an already-known infrastructure issue.
"""

ACTIVE_ALERTS = [
    {
        "site": "East Data Center",
        "issue": "VPN gateway packet loss > 12%",
        "since": "2026-07-09 07:58",
        "severity": "Warning",
        "related_cis": ["vpn-gw-east-01"],
    }
]


def get_active_alerts(keyword: str = None):
    """Mirrors: POST /zabbix/api_jsonrpc.php  method=problem.get"""
    if not keyword:
        return ACTIVE_ALERTS
    keyword = keyword.lower()
    return [a for a in ACTIVE_ALERTS if keyword in a["issue"].lower() or keyword in a["site"].lower()]
