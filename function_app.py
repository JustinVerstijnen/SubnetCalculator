import azure.functions as func

def calculate_subnet(ip, cidr):
    try:
        cidr = int(cidr)
        if cidr < 0 or cidr > 32:
            return None
    except:
        return None

    ip_parts = ip.split('.')
    if len(ip_parts) != 4:
        return None

    try:
        ip_parts = [int(part) for part in ip_parts]
        if any(part < 0 or part > 255 for part in ip_parts):
            return None
    except:
        return None

    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    mask_parts = [(mask >> 24) & 0xff, (mask >> 16) & 0xff, (mask >> 8) & 0xff, mask & 0xff]

    ip_num = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
    network_num = ip_num & mask
    network_parts = [(network_num >> 24) & 0xff, (network_num >> 16) & 0xff, (network_num >> 8) & 0xff, network_num & 0xff]

    broadcast_num = network_num | (~mask & 0xffffffff)
    broadcast_parts = [(broadcast_num >> 24) & 0xff, (broadcast_num >> 16) & 0xff, (broadcast_num >> 8) & 0xff, broadcast_num & 0xff]

    hosts = 2**(32 - cidr) - 2 if cidr < 31 else (1 if cidr == 31 else 0)

    return {
        'subnet_mask': '.'.join(str(part) for part in mask_parts),
        'network_address': '.'.join(str(part) for part in network_parts),
        'broadcast_address': '.'.join(str(part) for part in broadcast_parts),
        'number_of_hosts': hosts
    }

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        ip = req.params.get('ip')
        cidr = req.params.get('cidr')

        if not ip or not cidr:
            return func.HttpResponse(html_form, mimetype="text/html")

        result = calculate_subnet(ip, cidr)
        if not result:
            return func.HttpResponse(html_form + "<p style='color:red; text-align:center;'>Ongeldige invoer. Vul een geldig IPv4-adres en CIDR (0-32) in.</p>", mimetype="text/html")

        response_html = html_form + f"""
        <div class="result">
            <h2>Subnet Berekening Resultaat</h2>
            <p><strong>IP-adres:</strong> {ip}</p>
            <p><strong>CIDR:</strong> /{cidr}</p>
            <p><strong>Subnet Masker:</strong> {result['subnet_mask']}</p>
            <p><strong>Netwerkadres:</strong> {result['network_address']}</p>
            <p><strong>Broadcastadres:</strong> {result['broadcast_address']}</p>
            <p><strong>Aantal Hosts:</strong> {result['number_of_hosts']}</p>
        </div>
        """

        return func.HttpResponse(response_html, mimetype="text/html")
    except Exception as e:
        # Return een simpele foutmelding als iets misgaat
        return func.HttpResponse(f"<h1>Er is een fout opgetreden:</h1><pre>{str(e)}</pre>", status_code=500, mimetype="text/html")


html_form = """
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>IPv4 Subnet Calculator</title>
<style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f1f5f9;
        color: #334155;
        margin: 2em;
    }
    h1 {
        text-align: center;
        color: #1e293b;
    }
    form {
        background-color: #e2e8f0;
        padding: 1.5em;
        border-radius: 8px;
        max-width: 400px;
        margin: 0 auto 2em auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    label {
        display: block;
        margin-bottom: 0.5em;
        font-weight: bold;
        color: #0f172a;
    }
    input[type="text"], input[type="number"] {
        width: 100%;
        padding: 0.5em;
        border: 1px solid #94a3b8;
        border-radius: 4px;
        margin-bottom: 1em;
        font-size: 1em;
    }
    button {
        background-color: #22c55e;
        color: white;
        border: none;
        padding: 0.75em 1.5em;
        font-size: 1em;
        border-radius: 6px;
        cursor: pointer;
        width: 100%;
    }
    button:hover {
        background-color: #16a34a;
    }
    .result {
        background-color: #dcfce7;
        border: 1px solid #22c55e;
        max-width: 400px;
        margin: 0 auto;
        padding: 1em 1.5em;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(34, 197, 94, 0.25);
    }
</style>
</head>
<body>
<h1>IPv4 Subnet Calculator</h1>
<form method="get">
    <label for="ip">IP-adres:</label>
    <input type="text" id="ip" name="ip" placeholder="bijv. 192.168.1.0" required />
    <label for="cidr">CIDR (0-32):</label>
    <input type="number" id="cidr" name="cidr" min="0" max="32" placeholder="bijv. 24" required />
    <button type="submit">Bereken</button>
</form>
</body>
</html>
"""
