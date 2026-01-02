document.addEventListener('DOMContentLoaded', () => {
    const ipInput = document.getElementById('ip');
    const cidrSelect = document.getElementById('cidr');
    const ipPresets = document.getElementById('ip-presets');
    const exportBtn = document.getElementById('export-btn');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error-msg');
    const container = document.querySelector('.container');
    const learnBtn = document.getElementById('learn-btn');

    ipPresets.addEventListener('change', (e) => {
      const val = e.target.value.trim();
      if (val) {
        ipInput.value = val;
      }
    });
    if (learnBtn) {
      learnBtn.addEventListener('click', () => {
        window.open('https://justinverstijnen.nl/networking-fundametals/', '_blank', 'noopener,noreferrer');
      });
    }


    function isValidIp(ip) {
      const parts = ip.trim().split('.');
      if (parts.length !== 4) return false;
      for (const part of parts) {
        if (!/^\d+$/.test(part)) return false;
        const num = Number(part);
        if (num < 0 || num > 255) return false;
      }
      return true;
    }

    function toBinaryOctet(num) {
      return num.toString(2).padStart(8, '0');
    }

    function getIpClass(firstOctet) {
      if (firstOctet >= 0 && firstOctet <= 127) return 'A';
      if (firstOctet >= 128 && firstOctet <= 191) return 'B';
      if (firstOctet >= 192 && firstOctet <= 223) return 'C';
      if (firstOctet >= 224 && firstOctet <= 239) return 'D (Multicast)';
      if (firstOctet >= 240 && firstOctet <= 255) return 'E (Experimental)';
      return 'Unknown';
    }

    function getIpType(ipParts) {
      const [a,b,c,d] = ipParts;
      if (a === 10) return 'Private';
      if (a === 172 && b >= 16 && b <= 31) return 'Private';
      if (a === 192 && b === 168) return 'Private';
      if (a === 127) return 'Loopback';
      if (a === 169 && b === 254) return 'Link-local';
      if (a >= 224 && a <= 239) return 'Multicast';
      if (a === 255 && b === 255 && c === 255 && d === 255) return 'Broadcast';
      return 'Public';
    }

    function formatNumber(num) {
      // Use spaces as thousands separator (instead of commas)
      return num.toLocaleString('en-US').replace(/,/g, ' ');
    }

    function calculateSubnet(ip, cidr) {
      cidr = Number(cidr);
      if (cidr < 0 || cidr > 32) return null;

      const ipParts = ip.trim().split('.').map(Number);

      const mask = (0xffffffff >>> (32 - cidr)) << (32 - cidr);
      const maskParts = [
        (mask >>> 24) & 0xff,
        (mask >>> 16) & 0xff,
        (mask >>> 8) & 0xff,
        mask & 0xff
      ];

      const ipNum = (ipParts[0] << 24) + (ipParts[1] << 16) + (ipParts[2] << 8) + ipParts[3];
      const networkNum = ipNum & mask;
      const networkParts = [
        (networkNum >>> 24) & 0xff,
        (networkNum >>> 16) & 0xff,
        (networkNum >>> 8) & 0xff,
        networkNum & 0xff
      ];

      const broadcastNum = networkNum | (~mask >>> 0);
      const broadcastParts = [
        (broadcastNum >>> 24) & 0xff,
        (broadcastNum >>> 16) & 0xff,
        (broadcastNum >>> 8) & 0xff,
        broadcastNum & 0xff
      ];

      const hosts = cidr < 31 ? (2 ** (32 - cidr) - 2) : (cidr === 31 ? 2 : 1);

      let firstHost = null, lastHost = null;
      if (hosts > 0) {
        firstHost = [
          networkParts[0],
          networkParts[1],
          networkParts[2],
          networkParts[3] + 1
        ];
        lastHost = [
          broadcastParts[0],
          broadcastParts[1],
          broadcastParts[2],
          broadcastParts[3] -1
        ];
      } else if (cidr === 31) {
        firstHost = networkParts;
        lastHost = broadcastParts;
      } else {
        firstHost = networkParts;
        lastHost = networkParts;
      }

      const wildcardParts = maskParts.map(octet => 255 - octet);
      const binaryMask = maskParts.map(toBinaryOctet).join('.');
      const ipClass = getIpClass(ipParts[0]);
      const ipType = getIpType(ipParts);
      const shortNotation = networkParts.join('.') + '/' + cidr;

      return {
        subnet_mask: maskParts.join('.'),
        network_address: networkParts.join('.'),
        broadcast_address: broadcastParts.join('.'),
        number_of_hosts: hosts,
        formatted_hosts: formatNumber(hosts),
        usable_range: `${firstHost.join('.')} - ${lastHost.join('.')}`,
        wildcard_mask: wildcardParts.join('.'),
        binary_subnet_mask: binaryMask,
        ip_class: ipClass,
        ip_type: ipType,
        short_notation: shortNotation
      };
    }

    document.getElementById('subnet-form').addEventListener('submit', (e) => {
      e.preventDefault();

      const ip = ipInput.value.trim();
      const cidr = cidrSelect.value;

      errorDiv.style.display = 'none';
      resultDiv.style.display = 'none';
      exportBtn.style.display = 'none';
      errorDiv.textContent = '';
      resultDiv.innerHTML = '';

      if (!isValidIp(ip)) {
        errorDiv.textContent = 'Invalid IP address!';
        errorDiv.style.display = 'block';
        return;
      }
      if (!cidr) {
        errorDiv.textContent = 'Select a Subnet mask!';
        errorDiv.style.display = 'block';
        return;
      }

      const result = calculateSubnet(ip, cidr);
      if (!result) {
        errorDiv.textContent = 'Error calculating your subnet';
        errorDiv.style.display = 'block';
        return;
      }

      resultDiv.innerHTML = `
        <h2>Subnet Calculation Result:</h2>
        <table>
          <tr>
            <td><span class="tooltip">CIDR notation<span class="tooltip-text">CIDR (Classless Inter-Domain Routing) notation is used to specify IP addresses and their associated subnet masks. It combines the IP address and the prefix length into a single identifier (e.g., 10.0.0.0/8).</span></span>:</td>
            <td>${result.short_notation}</td>
          </tr>
          <tr>
            <td><span class="tooltip">IP Address<span class="tooltip-text">An IP address is a unique identifier for a device on a network, enabling communication between devices.</span></span>:</td>
            <td>${ip}</td>
          </tr>
          <tr>
            <td><span class="tooltip">Subnet Mask<span class="tooltip-text">A subnet mask is used to divide an IP address into network and host portions, determining which addresses are in the same subnet.</span></span>:</td>
            <td>${result.subnet_mask}</td>
          </tr>
          <tr>
            <td><span class="tooltip">CIDR Prefix<span class="tooltip-text">The CIDR prefix indicates the number of bits used to identify the network part of an IP address. For example, /24 means the first 24 bits are used for the network.</span></span>:</td>
            <td>/${cidr}</td>
          </tr>
          <tr>
            <td><span class="tooltip">Maximum Possible Hosts<span class="tooltip-text">This is the maximum number of hosts that can be assigned within the subnet, based on the subnet mask. It excludes the network and broadcast addresses.</span></span>:</td>
            <td>${result.formatted_hosts}</td>
          </tr>
          <tr>
            <td><span class="tooltip">Usable Address Range<span class="tooltip-text">The range of IP addresses available for devices within the subnet, excluding the network and broadcast addresses.</span></span>:</td>
            <td>${result.usable_range}</td>
          </tr>
          <tr>
            <td><span class="tooltip">Network Address<span class="tooltip-text">The network address is the first address in a subnet and is used to identify the subnet itself.</span></span>:</td>
            <td>${result.network_address}</td>
          </tr>
          <tr>
            <td><span class="tooltip">Broadcast Address<span class="tooltip-text">The broadcast address is used to send data to all devices within a subnet. It is the last address in the subnet.</span></span>:</td>
            <td>${result.broadcast_address}</td>
          </tr>
          <tr>
            <td><span class="tooltip">IP Class<span class="tooltip-text">IP classes (A, B, C, D, E) categorize IP address ranges for various purposes, such as private networks or public internet addressing.</span></span>:</td>
            <td>${result.ip_class}</td>
          </tr>
          <tr>
            <td><span class="tooltip">IP Type<span class="tooltip-text">The IP Type indicates whether the address is private, public, loopback, or multicast.</span></span>:</td>
            <td>${result.ip_type}</td>
          </tr>
          <tr>
            <td><span class="tooltip">Wildcard Mask<span class="tooltip-text">The wildcard mask is the inverse of the subnet mask, used in routing protocols like OSPF to define which bits are ignored when routing.</span></span>:</td>
            <td>${result.wildcard_mask}</td>
          </tr>
          <tr>
            <td><span class="tooltip">Binary Subnet Mask<span class="tooltip-text">The binary subnet mask represents the subnet mask in binary form, making it easier to understand the network structure.</span></span>:</td>
            <td>${result.binary_subnet_mask}</td>
          </tr>
        </table>
      `;

      if (!document.getElementById('subnet-table')) {
        const subnetTableHtml = `

          <div class="section-spacer"></div>
          <details id="subnet-table" class="ref-details">
            <summary>Subnets and sizes (click to open)</summary>
            <div class="table-wrapper reference-table">
              <table>
                <thead>
                  <tr>
                    <th>Prefix</th>
                    <th>Subnet mask</th>
                    <th>Usable addresses</th>
                  </tr>
                </thead>
                <tbody>
<tr><td><strong>Supernets (ISPs)</strong></td><td></td><td></td></tr>
                <tr><td>/0</td><td>0.0.0.0</td><td>Used as wildcard</td></tr>
                <tr><td>/1</td><td>128.0.0.0</td><td>2 147 483 646</td></tr>
                <tr><td>/2</td><td>192.0.0.0</td><td>1 073 741 822</td></tr>
                <tr><td>/3</td><td>224.0.0.0</td><td>536 870 910</td></tr>
                <tr><td>/4</td><td>240.0.0.0</td><td>268 435 454</td></tr>
                <tr><td>/5</td><td>248.0.0.0</td><td>134 217 726</td></tr>
                <tr><td>/6</td><td>252.0.0.0</td><td>67 108 862</td></tr>
                <tr><td>/7</td><td>254.0.0.0</td><td>33 554 430</td></tr>
                <tr><td><strong>Class A networks</strong></td><td></td><td></td></tr>
                <tr><td>/8</td><td>255.0.0.0</td><td>16 777 214</td></tr>
                <tr><td>/9</td><td>255.128.0.0</td><td>8 388 606</td></tr>
                <tr><td>/10</td><td>255.192.0.0</td><td>4 194 302</td></tr>
                <tr><td>/11</td><td>255.224.0.0</td><td>2 097 150</td></tr>
                <tr><td>/12</td><td>255.240.0.0</td><td>1 048 574</td></tr>
                <tr><td>/13</td><td>255.248.0.0</td><td>524 286</td></tr>
                <tr><td>/14</td><td>255.252.0.0</td><td>262 142</td></tr>
                <tr><td>/15</td><td>255.254.0.0</td><td>131 070</td></tr>
                <tr><td><strong>Class B networks</strong></td><td></td><td></td></tr>
                <tr><td>/16</td><td>255.255.0.0</td><td>65 534</td></tr>
                <tr><td>/17</td><td>255.255.128.0</td><td>32 766</td></tr>
                <tr><td>/18</td><td>255.255.192.0</td><td>16 382</td></tr>
                <tr><td>/19</td><td>255.255.224.0</td><td>8 190</td></tr>
                <tr><td>/20</td><td>255.255.240.0</td><td>4 094</td></tr>
                <tr><td>/21</td><td>255.255.248.0</td><td>2 046</td></tr>
                <tr><td>/22</td><td>255.255.252.0</td><td>1 022</td></tr>
                <tr><td>/23</td><td>255.255.254.0</td><td>510</td></tr>
                <tr><td><strong>Class C networks</strong></td><td></td><td></td></tr>
                <tr><td>/24</td><td>255.255.255.0</td><td>254</td></tr>
                <tr><td>/25</td><td>255.255.255.128</td><td>126</td></tr>
                <tr><td>/26</td><td>255.255.255.192</td><td>62</td></tr>
                <tr><td>/27</td><td>255.255.255.224</td><td>30</td></tr>
                <tr><td>/28</td><td>255.255.255.240</td><td>14</td></tr>
                <tr><td>/29</td><td>255.255.255.248</td><td>6</td></tr>
                <tr><td>/30</td><td>255.255.255.252</td><td>2</td></tr>
                <tr><td>/31</td><td>255.255.255.254</td><td>0</td></tr>
                <tr><td>/32</td><td>255.255.255.255</td><td>0</td></tr>

                </tbody>
              </table>
            </div>
          </details>

        `;
        resultDiv.insertAdjacentHTML('beforeend', subnetTableHtml);
      }
      resultDiv.style.display = 'block';
      exportBtn.style.display = 'inline-flex';
    });
    exportBtn.addEventListener('click', () => {
      // Clone current results so export matches the on-page (new) table design.
      const temp = document.createElement('div');
      temp.innerHTML = resultDiv.innerHTML;

      // Wrap the first (network result) table in the same table-wrapper used on-page.
      const firstTable = temp.querySelector('table');
      if (firstTable && !firstTable.closest('.table-wrapper')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-wrapper';
        firstTable.parentNode.insertBefore(wrapper, firstTable);
        wrapper.appendChild(firstTable);
      }

      const exportCss = `
        :root{--brand-blue:#8EAFDA;--brand-blue-hover:#637b99;--brand-green:#92DBA5;--brand-green-hover:#7ac58d;--bg:#f2f2f2;--text:#2e3440;--muted:#6b7280;--border:#d1d5db;--radius:8px;}
        *{box-sizing:border-box;}
        body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:var(--bg);margin:0;padding:2rem;color:var(--text);}
        .container{position:relative;max-width:945px;margin:5px auto;padding:20px;background:#fff;border-radius:var(--radius);box-shadow:0 0 15px rgba(0,0,0,.1);}
        .header{display:flex;align-items:center;justify-content:center;margin-bottom:8px;}
        .header img{max-width:50px;height:auto;}
        h1{text-align:center;font-weight:700;margin:10px 0;color:#1f2937;}
        .subtitle{text-decoration:none;;text-align:center;font-size:.95rem;color:var(--muted);margin:-6px 0 28px;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;}
        .table-wrapper{margin-top:14px;border-radius:10px;box-shadow:0 0 10px rgba(0,0,0,.1);background:#fff;}
        table{width:100%;border-collapse:separate;border-spacing:0;border-radius:10px;table-layout:fixed;}
        thead{background:#f8f9fa;}
        th,td{padding:15px;text-align:left;vertical-align:top;word-break:break-word;overflow-wrap:anywhere;}
        tbody tr:nth-child(even){background:#f6f6f6;}
        th:first-child{white-space:nowrap;}
        .tooltip{position:relative;cursor:help;text-decoration:none;font-weight:700;color:#111827;}
        .tooltip .tooltip-text{font-weight:400;visibility:hidden;opacity:0;position:absolute;left:0;top:calc(100% + 8px);width:min(360px,70vw);background:#8EAFDA;color:#ffffff;padding:10px 12px;border-radius:10px;font-size:13px;line-height:1.35;box-shadow:0 12px 28px rgba(0,0,0,.25);transition:opacity .15s ease;z-index:20;}
        .tooltip:hover .tooltip-text{visibility:visible;opacity:1;}
        details{margin-top:0;}
        .ref-details > summary{list-style:none;cursor:pointer;font-weight:700;margin:0;padding:12px 14px;border:1px solid var(--border);border-radius:10px;background:#f8f9fa;display:flex;align-items:center;justify-content:space-between;}
        .ref-details > summary::-webkit-details-marker{display:none;}
        .ref-details > summary::after{content:'▸';font-weight:900;color:#111827;}
        .ref-details[open] > summary::after{content:'▾';}
        .ref-details[open] > summary{border-bottom-left-radius:0;border-bottom-right-radius:0;}
        .ref-details .reference-table{margin-top:0;border-top-left-radius:0;border-top-right-radius:0;}
        .ref-details:not([open]) .reference-table{display:none;}
        .section-spacer{height:40px;}
        .footer{margin-top:24px;text-align:center;font-size:9px;color:#777;}
        .footer a{color:#777;text-decoration:none;}
        .footer a:hover{color:#777;text-decoration:none;}
      `;

      const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Subnet Calculation - justinverstijnen.nl</title>
  <style>${exportCss}</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <a href="https://justinverstijnen.nl" target="_blank" rel="noopener noreferrer">
        <img src="https://justinverstijnen.nl/wp-content/uploads/2025/04/cropped-Logo-2.0-Transparant.png" alt="Justin Verstijnen Logo" width="50" height="50" />
      </a>
    </div>
    <h1>Subnet Calculation</h1>
    <p class="subtitle">Exported subnet calculation using the <a href="https://subnet.justinverstijnen.nl" target="_blank" rel="noopener noreferrer">Justin Verstijnen Subnet Calculator.</a></p>
    ${temp.innerHTML}
    <div class="footer">
      <a href="https://github.com/JustinVerstijnen/SubnetCalculator" target="_blank" rel="noopener noreferrer">
        &copy; ${new Date().getFullYear()} Subnet Calculator by Justin Verstijnen. Click here to visit GitHub project.
      </a>
    </div>
  </div>
</body>
</html>`;

      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'subnet-result.html';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    });
});
