import azure.functions as func

def calculate_subnet(ip, cidr):
    try:
        cidr = int(cidr)
        if cidr < 0 or cidr > 32:
            return {"error": "CIDR moet tussen 0 en 32 liggen."}
    except:
        return {"error": "Ongeldige CIDR waarde."}

    ip_parts = ip.split('.')
    if len(ip_parts) != 4:
        return {"error": "Ongeldig IPv4-adres."}

    try:
        ip_parts = [int(part) for part in ip_parts]
        if any(part < 0 or part > 255 for part in ip_parts):
            return {"error": "Ongeldig IPv4-adres."}
    except:
        return {"error": "Ongeldig IPv4-adres."}

    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    mask_parts = [(mask >> 24) & 0xff, (mask >> 16) & 0xff, (mask >> 8) & 0xff, mask & 0xff]

    ip_num = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
    network_num = ip_num & mask
    network_parts = [(network_num >> 24) & 0xff, (network_num >> 16) & 0xff, (network_num >> 8) & 0xff, network_num & 0xff]

    broadcast_num = network_num | (~mask & 0xffffffff)
    broadcast_parts = [(broadcast_num >> 24) & 0xff, (broadcast_num >> 16) & 0xff, (broadcast_num >> 8) & 0xff, broadcast_num & 0xff]

    hosts = 2**(32 - cidr) - 2 if cidr < 31 else (1 if cidr == 31 else 0)

    return {
        "subnet_mask": '.'.join(str(part) for part in mask_parts),
        "network_address": '.'.join(str(part) for part in network_parts),
        "broadcast_address": '.'.join(str(part) for part in broadcast_parts),
        "number_of_hosts": hosts
    }

def main(req: func.HttpRequest) -> func.HttpResponse:
    ip = req.params.get('ip')
    cidr = req.params.get('cidr')

    if not ip or not cidr:
        return func.HttpResponse(
            '{"error":"Geef IP-adres en CIDR op als query parameters."}',
            status_code=400,
            mimetype="application/json"
        )

    result = calculate_subnet(ip, cidr)

    import json
    return func.HttpResponse(
        json.dumps(result),
        status_code=200 if "error" not in result else 400,
        mimetype="application/json"
    )
