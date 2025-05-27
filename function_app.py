import azure.functions as func
import dns.resolver
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

def get_txt_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'TXT')
        return [r.to_text().strip('"') for r in records]
    except Exception:
        return ["Not found"]

def get_ns_servers(domain):
    try:
        records = dns.resolver.resolve(domain, 'NS')
        return [str(r.target).strip('.') for r in records]
    except Exception:
        return ["Not found"]

def get_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return [str(r.exchange).strip('.') for r in records]
    except Exception:
        return ["No MX record found"]

def get_ds_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'DS')
        return [r.to_text() for r in records]
    except Exception:
        return ["No DS record found or domain does not support DNSSEC."]

def check_dnskey_exists(domain):
    try:
        dns.resolver.resolve(domain, 'DNSKEY')
        return True
    except Exception:
        return False

@app.route(
    route="/",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def dns_mega_tool(req: func.HttpRequest) -> func.HttpResponse:
    domain = req.params.get('domain')
    if not domain:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DNS MEGAtool - justinverstijnen.nl</title>
            <style>
                body {
                    font-family: 'Segoe UI', sans-serif;
                    background: #f4f6f8;
                    padding: 2em;
                    max-width: 1000px;
                    margin: auto;
                }
                h2 {
                    color: #333;
                    text-align: center;
                }
                input, button {
                    padding: 0.6em;
                    font-size: 1em;
                    margin: 0.5em 0;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                button {
                    background-color: #88B0DC;
                    color: white;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #005A9E;
                }
                .btn-icon::before {
                    margin-right: 0.5em;
                }
                table {
                    margin: 2em auto;
                    width: 90%;
                    border-collapse: collapse;
                    background: white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                th, td {
                    padding: 1em;
                    border-bottom: 1px solid #eee;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background: #f0f2f5;
                }
                .enabled { color: green; font-weight: bold; }
                .disabled { color: red; font-weight: bold; }
                .small { font-size: 0.9em; color: #444; }
                .dnsinfo {
                    margin-top: 2em;
                    padding: 1em;
                    background-color: #eaf4ff;
                    border-left: 4px solid #0078D4;
                    font-size: 0.95em;
                    max-width: 90%;
                    margin-left: auto;
                    margin-right: auto;
                }
                .criteria {
                    margin-top: 1em;
                    padding: 1em;
                    background-color: #e6f7e6;
                    border-left: 4px solid #4CAF50;
                    font-size: 0.95em;
                    max-width: 90%;
                    margin-left: auto;
                    margin-right: auto;
                }
                .more { color: blue; cursor: pointer; text-decoration: underline; }
                .tooltip {
  position: relative;
  display: inline-block;
  cursor: help;
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: 250px;
  background-color: #333;
  color: #fff;
  text-align: left;
  border-radius: 6px;
  padding: 0.8em;
  position: absolute;
  z-index: 1;
  bottom: 125%; 
  left: 0;
  opacity: 0;
  transition: opacity 0.3s;
  font-size: 0.85em;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}
            </style>
        </head>
        <body>
            <div style="text-align:center; margin-bottom: 1em;">
                <a href="https://justinverstijnen.nl" target="_blank"> <img src="https://justinverstijnen.nl/wp-content/uploads/2025/04/cropped-Logo-2.0-Transparant.png" alt="Logo" style="height:50px;" /></a>
            </div>

            <h2>DNS MEGAtool</h2>
            <p style="text-align:center;">This tool checks multiple DNS records and their configuration for your domain.</p>
            <div style="text-align:center;">
                <form id="SubmitButton">
  <input type="text" id="domainInput" placeholder="example.com" />
  <button type="submit" id="submitButton" class="btn-icon check-btn">
    <svg style="height:1em;vertical-align:middle;margin-right:0.5em;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
      <path d="M10 2a8 8 0 105.293 14.293l4.707 4.707 1.414-1.414-4.707-4.707A8 8 0 0010 2zm0 2a6 6 0 110 12 6 6 0 010-12z"/>
    </svg>
    Check
  </button>
  <button id="exportBtn" type="button" class="btn-icon export-btn" onclick="download()" style="background-color: #92DBA5; display: none;">
                    <svg style="height:1em;vertical-align:middle;margin-right:0.5em;" xmlns="http://www.w3.org/2000/svg" fill="white" viewBox="0 0 24 24"><path d="M12 16.5l6-6-1.41-1.42L13 12.67V4h-2v8.67l-3.59-3.59L6 10.5l6 6z"/></svg>
                    Export
                </button>
</form>

<script>
  const form = document.getElementById('SubmitButton');

  form.addEventListener('submit', function(event) {
    event.preventDefault();
    lookup();
  });

  function lookup() {
    const domain = document.getElementById('domainInput').value;
    console.log("Search for:", domain);
  }
</script>
            </div>

            <div id="result"></div>

            <script>
                async function lookup() {
                    const domain = document.getElementById('domainInput').value.trim();
                    if (!domain) return;
                    const res = await fetch(`?domain=${domain}`);
                    const data = await res.json();
                    window.latestResult = data;
                    document.getElementById("exportBtn").style.display = "inline-block";
                    const resultEl = document.getElementById('result');
                    resultEl.innerHTML = "";

                    const formatRow = (label, enabled, value) => {
    const descriptions = {
        "MX": "Checks if valid MX records are configured for the domain.",
        "SPF": "Checks if a valid SPF record with v=spf1 and a Hardfail (-all) is present.",
        "DKIM": "Looks for valid DKIM records and active selectors.",
        "DMARC": "Checks if a DMARC record exists with policy p=reject.",
        "MTA-STS": "Checks if a valid MTA-STS TXT record exists.",
        "DNSSEC": "Checks if both DNSKEY and DS records are present."
    };
    const links = {
        "MX": "https://justinverstijnen.nl/enhance-email-security-with-spf-dkim-dmarc#mx",
        "SPF": "https://justinverstijnen.nl/enhance-email-security-with-spf-dkim-dmarc#spf",
        "DKIM": "https://justinverstijnen.nl/enhance-email-security-with-spf-dkim-dmarc#dkim",
        "DMARC": "https://justinverstijnen.nl/enhance-email-security-with-spf-dkim-dmarc#dmarc",
        "MTA-STS": "https://justinverstijnen.nl/what-is-mta-sts-and-how-to-protect-your-email-flow#mta-sts",
        "DNSSEC": "https://justinverstijnen.nl/configure-dnssec-and-smtp-dane-with-exchange-online-microsoft-365#dnssec"
    };

    const shortValue = value.length > 100 ? value.slice(0, 100) + '...' : value;
    const escaped = value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#39;");

    let moreLink = '';
    let valueToShow = shortValue;

    if (value.length > 100) {
        const id = `detail-${label.toLowerCase()}`;
        moreLink = `<span class='more' onclick="document.getElementById('${id}').style.display='block'; this.parentElement.querySelector('.short').style.display='none'; this.style.display='none';">View more</span>`;
        valueToShow = `<span class='short'>${shortValue}</span><div id='${id}' style='display:none; word-break: break-word;'>${escaped}</div>`;
    }

    const tooltip = `
        <div class='tooltip'><strong>${label}</strong>
            <div class='tooltiptext'>${descriptions[label]}<br/>
                <a href='${links[label]}' target='_blank' style='color:#aad;'>More info</a>
            </div>
        </div>`;

    return `<tr><td>${tooltip}</td><td class='${enabled ? 'enabled' : 'disabled'}'>${enabled ? '✅' : '❌'}</td><td><div class='small'>${valueToShow} ${moreLink}</div></td></tr>`;
};
                    const spf = data.SPF.find(r => r.includes("v=spf1")) || "No SPF record found";
                    const spfIsStrict = spf.includes("-all");
                    const dmarc = data.DMARC.find(r => r.includes("v=DMARC1")) || "No DMARC record found";
                    const mta = data.MTA_STS.find(r => r.includes("v=STSv1")) || "No MTA-STS record found";
                    const dkim = data.DKIM.record.find(r => r.includes("v=DKIM1")) || "No DKIM record(s) found";
                    const hasDKIM = data.DKIM.valid_selector !== null;
                    const dnssec = data.DNSSEC;
                    const ds = data.DS[0] || "No DS record found or domain does not support DNSSEC.";
                    const mx = data.MX.join(", ") || "No MX record found";

                    resultEl.innerHTML = `
                        <table>
                            <tr><th>Technology</th><th>Status</th><th>DNS Record</th></tr>
                            ${formatRow("MX", mx !== "Not found", mx)}
                            ${formatRow("SPF", spfIsStrict, spf)}
                            ${formatRow("DKIM", hasDKIM, dkim)}
                            ${formatRow("DMARC", dmarc.includes("p=reject"), dmarc)}
                            ${formatRow("MTA-STS", mta.includes("v=STSv1"), mta)}
                            ${formatRow("DNSSEC", dnssec, ds)}
                        </table>
                        <div class="dnsinfo">
                            <strong>Authoritative DNS servers for ${data.domain}:</strong><br/>
                            ${data.NS.join("<br/>")}
                            <br/><br/>
                            <strong>WHOIS:</strong> <a href="https://who.is/whois/${data.domain}" target="_blank">View WHOIS info</a>
                        </div>
                        <div class="criteria">
                            <strong>Extra information</strong><br/><br/>
                            Thank you for using DNS MEGAtool. The checks are performed have the following criteria:<br/><br/>
                            - <strong>MX record</strong>: Checks if there is a MX record for the domain and shows the value.<br/>
                            - <strong>SPF record</strong>: Checks if a valid SPF record and a hardfail (-all) is present.<br/>
                            - <strong>DKIM record</strong>: Checks if there are DKIM records for the domain and shows the values.<br/>
                            - <strong>DMARC record</strong>: Checks if "Reject" is configured as DMARC policy to make it the most effective.<br/>
                            - <strong>MTA-STS record</strong>: Checks if there is a MTA-STS record for the domain and shows the value.<br/>
                            - <strong>DNSSEC</strong>: Checks if both DNSKEY and DS records are present.<br><br>
                            Hover on the technology names to get more information and links to the articles and get the information to know and configure them.<br><br>
                            Issues with this tool? Report them at <a href="mailto:info@justinverstijnen.nl">info@justinverstijnen.nl</a><br><br>
                            Thank you for using this tool.
                        </div>
                    `;
                }

                const toolVersion = "v1.1";
                
function download() {
    const data = window.latestResult;
    if (!data) return alert("Please run a check first.");

    const renderRow = (label, records, isActive = true) => {
        const statusClass = isActive ? "enabled" : "disabled";
        const statusIcon = isActive ? "✅" : "❌";
        const value = Array.isArray(records) ? records.join("<br>") : records;
        return `
            <tr>
                <td><strong>${label}</strong></td>
                <td class="${statusClass}">${statusIcon}</td>
                <td class="small">${value}</td>
            </tr>
        `;
    };

    const spf = data.SPF.find(r => r.includes("v=spf1")) || "No SPF record found";
    const spfIsStrict = spf.includes("-all");
    const dmarc = data.DMARC.find(r => r.includes("v=DMARC1")) || "No DMARC record found";
    const mta = data.MTA_STS.find(r => r.includes("v=STSv1")) || "No MTA-STS record found";
    const dkim = data.DKIM.record.find(r => r.includes("v=DKIM1")) || "No DKIM record(s) found";
    const hasDKIM = data.DKIM.valid_selector !== null;
    const dnssec = data.DNSSEC;
    const ds = data.DS[0] || "No DS record found or domain does not support DNSSEC.";
    const mx = data.MX.join("<br>") || "No MX record found";

    const htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DNS MEGAtool Report - justinverstijnen.nl</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #f4f6f8;
            padding: 2em;
            margin: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 2em;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
        }
        .logo {
            text-align: center;
            margin-bottom: 2em;
        }
        .logo img {
            height: 50px;
        }
        h2 {
            text-align: center;
            color: #333;
        }
        p {
            text-align: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 2em;
        }
        th, td {
            padding: 1em;
            border-bottom: 1px solid #eee;
            text-align: left;
        }
        td.small {
            font-size: 0.9em;
            color: #444;
            word-break: break-word;
            white-space: normal;
        }
        th {
            background: #f0f2f5;
        }
        .enabled { color: green; font-weight: bold; }
        .disabled { color: red; font-weight: bold; }
        .footer {
            text-align: center;
            margin-top: 3em;
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <a href="https://justinverstijnen.nl" target="_blank">
                <img src="https://justinverstijnen.nl/wp-content/uploads/2025/04/cropped-Logo-2.0-Transparant.png" alt="Logo" />
            </a>
        </div>
        <h2>DNS MEGAtool Report v1.1</h2>
        <p>Report of domain: <strong>${data.domain}</strong></p>
        <table>
            <tr><th>Technology</th><th>Status</th><th>DNS Record</th></tr>
            ${renderRow("MX", data.MX, mx !== "No MX record found")}
            ${renderRow("SPF", spf, spfIsStrict)}
            ${renderRow("DKIM", dkim, hasDKIM)}
            ${renderRow("DMARC", dmarc, dmarc.includes("p=reject"))}
            ${renderRow("MTA-STS", mta, mta.includes("v=STSv1"))}
            ${renderRow("DNSSEC", ds, dnssec)}
        </table>

        <div style="margin-top: 2em; padding: 1em; background-color: #eaf4ff; border-left: 4px solid #0078D4; font-size: 0.95em;">
            <strong>Authoritative DNS servers for ${data.domain}:</strong><br/>
            ${data.NS.join("<br/>")}<br><br>
            <strong>WHOIS:</strong> <a href="https://who.is/whois/${data.domain}" target="_blank">View WHOIS info</a>
        </div>

        <div class="footer">
            Report generated with <a href="https://dnsmegatool.justinverstijnen.nl" target="_blank">DNS MEGAtool</a><br/>
            &copy; ${new Date().getFullYear()} justinverstijnen.nl
        </div>
    </div>
</body>
</html>
`;

    const blob = new Blob([htmlContent], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dns-report-${data.domain}.html`;
    a.click();
    URL.revokeObjectURL(url);
}
            </script>
        </body>
        </html>
        """
        return func.HttpResponse(html, mimetype="text/html")

    spf = get_txt_record(domain)
    dmarc = get_txt_record(f"_dmarc.{domain}")
    mta_sts = get_txt_record(f"_mta-sts.{domain}")
    ns = get_ns_servers(domain)
    ds = get_ds_record(domain)
    dnskey_exists = check_dnskey_exists(domain)
    dnssec = dnskey_exists and ds and not ds[0].startswith("No ")
    mx = get_mx_record(domain)

    dkim_selectors = ["selector1", "selector2", "default"]
    dkim_records = {}
    for sel in dkim_selectors:
        full_name = f"{sel}._domainkey.{domain}"
        result = get_txt_record(full_name)
        if any("v=DKIM1" in r for r in result):
            dkim_records["valid_selector"] = sel
            dkim_records["record"] = result
            break
    else:
        dkim_records["valid_selector"] = None
        dkim_records["record"] = ["Not found"]

    result = {
        "domain": domain,
        "SPF": spf,
        "DMARC": dmarc,
        "DKIM": dkim_records,
        "MTA_STS": mta_sts,
        "NS": ns,
        "DNSSEC": dnssec,
        "DS": ds,
        "MX": mx
    }

    return func.HttpResponse(
        json.dumps(result, indent=2),
        mimetype="application/json"
    )
