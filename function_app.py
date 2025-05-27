import azure.functions as func
from flask import Flask, request, render_template_string
import ipaddress

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>IP Subnet Calculator</title>
</head>
<body>
    <h2>IPv4 Subnet Calculator</h2>
    <form method="post">
        <label>IPv4 Address:</label>
        <input type="text" name="ipv4_address" value="{{ ipv4_address or '' }}" required>
        <label>Subnet Mask (CIDR or dotted):</label>
        <input type="text" name="ipv4_subnet" value="{{ ipv4_subnet or '' }}" required>
        <button type="submit" name="action" value="ipv4">Calculate IPv4</button>
    </form>

    {% if ipv4_result %}
        <h3>IPv4 Result:</h3>
        {% if ipv4_is_error %}
            <p style="color:red;">{{ ipv4_result }}</p>
        {% else %}
            <ul>
                <li>Network: {{ ipv4_result.network }}</li>
                <li>Broadcast: {{ ipv4_result.broadcast }}</li>
                <li>Netmask: {{ ipv4_result.netmask }}</li>
                <li>Hostmask: {{ ipv4_result.hostmask }}</li>
                <li>Total hosts: {{ ipv4_result.num_addresses }}</li>
                <li>Usable hosts: {{ ipv4_result.num_addresses - 2 if ipv4_result.num_addresses > 2 else 0 }}</li>
                <li>First usable IP: {{ ipv4_result.network + 1 if ipv4_result.num_addresses > 2 else 'N/A' }}</li>
                <li>Last usable IP: {{ ipv4_result.broadcast - 1 if ipv4_result.num_addresses > 2 else 'N/A' }}</li>
            </ul>
        {% endif %}
    {% endif %}

    <hr>

    <h2>IPv6 Subnet Calculator</h2>
    <form method="post">
        <label>IPv6 Address:</label>
        <input type="text" name="ipv6_address" value="{{ ipv6_address or '' }}" required>
        <label>Prefix Length (e.g. /64):</label>
        <input type="text" name="ipv6_prefix" value="{{ ipv6_prefix or '' }}" required>
        <button type="submit" name="action" value="ipv6">Calculate IPv6</button>
    </form>

    {% if ipv6_result %}
        <h3>IPv6 Result:</h3>
        {% if ipv6_is_error %}
            <p style="color:red;">{{ ipv6_result }}</p>
        {% else %}
            <ul>
                <li>Network: {{ ipv6_result.network }}</li>
                <li>Num addresses: {{ ipv6_result.num_addresses }}</li>
                <li>Prefix length: {{ ipv6_result.prefixlen }}</li>
            </ul>
        {% endif %}
    {% endif %}

</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    ipv4_result = None
    ipv4_is_error = False
    ipv6_result = None
    ipv6_is_error = False
    ipv4_address = ipv4_subnet = ipv6_address = ipv6_prefix = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'ipv4':
            ipv4_address = request.form.get('ipv4_address')
            ipv4_subnet = request.form.get('ipv4_subnet')
            try:
                if '/' in ipv4_subnet:
                    network = ipaddress.IPv4Network(f"{ipv4_address}{ipv4_subnet}", strict=False)
                else:
                    network = ipaddress.IPv4Network(f"{ipv4_address}/{ipv4_subnet}", strict=False)
                ipv4_result = network
            except Exception as e:
                ipv4_result = f"Error: {e}"
                ipv4_is_error = True

        elif action == 'ipv6':
            ipv6_address = request.form.get('ipv6_address')
            ipv6_prefix = request.form.get('ipv6_prefix')
            try:
                if not ipv6_prefix.startswith('/'):
                    ipv6_prefix = '/' + ipv6_prefix
                network = ipaddress.IPv6Network(f"{ipv6_address}{ipv6_prefix}", strict=False)
                ipv6_result = network
            except Exception as e:
                ipv6_result = f"Error: {e}"
                ipv6_is_error = True

    return render_template_string(
        HTML,
        ipv4_result=ipv4_result,
        ipv4_is_error=ipv4_is_error,
        ipv6_result=ipv6_result,
        ipv6_is_error=ipv6_is_error,
        ipv4_address=ipv4_address,
        ipv4_subnet=ipv4_subnet,
        ipv6_address=ipv6_address,
        ipv6_prefix=ipv6_prefix
    )

def main(req: func.HttpRequest) -> func.HttpResponse:
    environ = req.get_wsgi_environ()
    response_status = None
    response_headers = []

    def start_response(status, headers):
        nonlocal response_status, response_headers
        response_status = status
        response_headers = headers
        return lambda x: None

    result = app.wsgi_app(environ, start_response)
    body = b''.join(result)

    status_code = int(response_status.split()[0])
    headers = {k: v for k, v in response_headers}

    return func.HttpResponse(body, status_code=status_code, headers=headers)
