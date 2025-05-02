import json

def get_copy_trade_template(all_candidates):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Copy Trade Candidates - LumenBro</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            ::-webkit-scrollbar-track {{
                background: #f1f1f1;
            }}
            ::-webkit-scrollbar-thumb {{
                background: #4CAF50;
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: #45a049;
            }}
            .truncate {{
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                cursor: pointer;
            }}
            .expanded {{
                white-space: normal;
                overflow: visible;
                text-overflow: clip;
            }}
            th, td {{
                padding: 8px 12px;
                font-size: 0.875rem;
                word-break: break-word;
            }}
            @media (max-width: 640px) {{
                .hide-on-mobile {{
                    display: none;
                }}
                th, td {{
                    padding: 6px 8px;
                    font-size: 0.75rem;
                }}
            }}
        </style>
    </head>
    <body class="bg-gray-100 font-sans">
        <div class="container mx-auto px-4 py-6">
            <h1 class="text-2xl font-bold text-center text-gray-800 mb-6">Copy Trade Candidates</h1>
            <div class="overflow-x-auto shadow-lg rounded-lg">
                <table id="candidates-table" class="min-w-full bg-white border border-gray-200">
                    <thead>
                        <tr class="bg-green-500 text-white">
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="source_account">Source Account</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="net_xlm_change">Net XLM Change</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="num_swaps">Num Swaps</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="total_volume_xlm">Total Volume XLM</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer hide-on-mobile" data-sort="per_swap_profit">Per Swap Profit</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer hide-on-mobile" data-sort="daily_swaps">Daily Swaps</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer hide-on-mobile" data-sort="pair_diversity">Pair Diversity</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer hide-on-mobile" data-sort="asset_pairs">Asset Pairs</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="score">Score</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer hide-on-mobile" data-sort="risk_level">Risk Level</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer hide-on-mobile" data-sort="trade_type">Trade Type</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold">Recommendation</th>
                        </tr>
                    </thead>
                    <tbody id="candidates-body" class="text-gray-700"></tbody>
                </table>
            </div>
        </div>

        <script>
            const candidates = {json.dumps(all_candidates)};
            const tbody = document.getElementById('candidates-body');
            candidates.forEach(candidate => {{
                const row = document.createElement('tr');
                row.className = 'border-t border-gray-200 hover:bg-gray-50';
                row.innerHTML = `
                    <td class="py-2 px-3 text-xs truncate max-w-[150px]" onclick="this.classList.toggle('expanded')">${{candidate.source_account}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.net_xlm_change.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.num_swaps}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.total_volume_xlm.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs hide-on-mobile">${{candidate.per_swap_profit.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs hide-on-mobile">${{candidate.daily_swaps.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs hide-on-mobile">${{candidate.pair_diversity}}</td>
                    <td class="py-2 px-3 text-xs truncate max-w-[150px] hide-on-mobile" onclick="this.classList.toggle('expanded')">${{candidate.asset_pairs.join(', ')}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.score.toFixed(4)}}</td>
                    <td class="py-2 px-3 text-xs hide-on-mobile">${{candidate.risk_level}}</td>
                    <td class="py-2 px-3 text-xs hide-on-mobile">${{candidate.trade_type}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.recommendation}}</td>
                `;
                tbody.appendChild(row);
            }});

            document.querySelectorAll('th').forEach(header => {{
                header.addEventListener('click', () => {{
                    const table = header.closest('table');
                    const tbody = table.querySelector('tbody');
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    const sortKey = header.getAttribute('data-sort');
                    const isNumeric = ['net_xlm_change', 'num_swaps', 'total_volume_xlm', 'per_swap_profit', 'daily_swaps', 'pair_diversity', 'score'].includes(sortKey);
                    if (!sortKey) return;

                    const direction = header.classList.contains('sort-asc') ? -1 : 1;
                    document.querySelectorAll('th').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
                    header.classList.add(direction === 1 ? 'sort-asc' : 'sort-desc');

                    rows.sort((a, b) => {{
                        let aValue, bValue;
                        switch (sortKey) {{
                            case 'source_account': aValue = a.cells[0].textContent; bValue = b.cells[0].textContent; break;
                            case 'net_xlm_change': aValue = parseFloat(a.cells[1].textContent); bValue = parseFloat(a.cells[1].textContent); break;
                            case 'num_swaps': aValue = parseInt(a.cells[2].textContent); bValue = parseInt(a.cells[2].textContent); break;
                            case 'total_volume_xlm': aValue = parseFloat(a.cells[3].textContent); bValue = parseFloat(a.cells[3].textContent); break;
                            case 'per_swap_profit': aValue = parseFloat(a.cells[4].textContent); bValue = parseFloat(a.cells[4].textContent); break;
                            case 'daily_swaps': aValue = parseFloat(a.cells[5].textContent); bValue = parseFloat(a.cells[5].textContent); break;
                            case 'pair_diversity': aValue = parseInt(a.cells[6].textContent); bValue = parseInt(a.cells[6].textContent); break;
                            case 'asset_pairs': aValue = a.cells[7].textContent; bValue = b.cells[7].textContent; break;
                            case 'score': aValue = parseFloat(a.cells[8].textContent); bValue = parseFloat(a.cells[8].textContent); break;
                            case 'risk_level': aValue = a.cells[9].textContent; bValue = b.cells[9].textContent; break;
                            case 'trade_type': aValue = a.cells[10].textContent; bValue = b.cells[10].textContent; break;
                        }}
                        if (isNumeric) {{
                            return (bValue - aValue) * direction;
                        }} else {{
                            return aValue.localeCompare(bValue) * direction;
                        }}
                    }});

                    while (tbody.firstChild) {{
                        tbody.removeChild(tbody.firstChild);
                    }}
                    rows.forEach(row => tbody.appendChild(row));
                }});
            }});
        </script>
    </body>
    </html>
    """

def get_domain_rankings_template(domain_rankings):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Domain Wallet Rankings - LumenBro</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            ::-webkit-scrollbar-track {{
                background: #f1f1f1;
            }}
            ::-webkit-scrollbar-thumb {{
                background: #4CAF50;
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: #45a049;
            }}
            .truncate {{
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                cursor: pointer;
            }}
            .expanded {{
                white-space: normal;
                overflow: visible;
                text-overflow: clip;
            }}
            th, td {{
                padding: 8px 12px;
                font-size: 0.875rem;
                word-break: break-word;
            }}
            @media (max-width: 640px) {{
                .hide-on-mobile {{
                    display: none;
                }}
                th, td {{
                    padding: 6px 8px;
                    font-size: 0.75rem;
                }}
            }}
        </style>
    </head>
    <body class="bg-gray-100 font-sans">
        <div class="container mx-auto px-4 py-6">
            <h1 class="text-2xl font-bold text-center text-gray-800 mb-6">Domain Wallet Rankings (Meme Assets)</h1>
            <div class="overflow-x-auto shadow-lg rounded-lg">
                <table id="rankings-table" class="min-w-full bg-white border border-gray-200">
                    <thead>
                        <tr class="bg-green-500 text-white">
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="source_account">Source Account</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="num_swaps">Num Swaps</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="xlm_inflows">XLM Inflows</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="xlm_outflows">XLM Outflows</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="net_xlm_flow">Net XLM Flow</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold hide-on-mobile">Assets Traded</th>
                        </tr>
                    </thead>
                    <tbody id="rankings-body" class="text-gray-700"></tbody>
                </table>
            </div>
        </div>

        <script>
            const rankings = {json.dumps(domain_rankings)};
            const tbody = document.getElementById('rankings-body');
            rankings.forEach(ranking => {{
                const assetsTraded = Object.entries(ranking.assets_traded).map(([asset, data]) => 
                    `${{asset}}: ${{data.num_swaps}} swaps, In: ${{data.xlm_inflows.toFixed(2)}}, Out: ${{data.xlm_outflows.toFixed(2)}}`
                ).join('\\n');
                const row = document.createElement('tr');
                row.className = 'border-t border-gray-200 hover:bg-gray-50';
                row.innerHTML = `
                    <td class="py-2 px-3 text-xs truncate max-w-[150px]" onclick="this.classList.toggle('expanded')">${{ranking.source_account}}</td>
                    <td class="py-2 px-3 text-xs">${{ranking.num_swaps}}</td>
                    <td class="py-2 px-3 text-xs">${{ranking.xlm_inflows.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs">${{ranking.xlm_outflows.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs">${{ranking.net_xlm_flow.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs hide-on-mobile">${{assetsTraded}}</td>
                `;
                tbody.appendChild(row);
            }});

            document.querySelectorAll('th').forEach(header => {{
                header.addEventListener('click', () => {{
                    const table = header.closest('table');
                    const tbody = table.querySelector('tbody');
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    const sortKey = header.getAttribute('data-sort');
                    const isNumeric = ['num_swaps', 'xlm_inflows', 'xlm_outflows', 'net_xlm_flow'].includes(sortKey);
                    if (!sortKey) return;

                    const direction = header.classList.contains('sort-asc') ? -1 : 1;
                    document.querySelectorAll('th').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
                    header.classList.add(direction === 1 ? 'sort-asc' : 'sort-desc');

                    rows.sort((a, b) => {{
                        let aValue, bValue;
                        switch (sortKey) {{
                            case 'source_account': aValue = a.cells[0].textContent; bValue = b.cells[0].textContent; break;
                            case 'num_swaps': aValue = parseInt(a.cells[1].textContent); bValue = parseInt(a.cells[1].textContent); break;
                            case 'xlm_inflows': aValue = parseFloat(a.cells[2].textContent); bValue = parseFloat(a.cells[2].textContent); break;
                            case 'xlm_outflows': aValue = parseFloat(a.cells[3].textContent); bValue = parseFloat(a.cells[3].textContent); break;
                            case 'net_xlm_flow': aValue = parseFloat(a.cells[4].textContent); bValue = parseFloat(a.cells[4].textContent); break;
                        }}
                        if (isNumeric) {{
                            return (bValue - aValue) * direction;
                        }} else {{
                            return aValue.localeCompare(bValue) * direction;
                        }}
                    }});

                    while (tbody.firstChild) {{
                        tbody.removeChild(tbody.firstChild);
                    }}
                    rows.forEach(row => tbody.appendChild(row));
                }});
            }});
        </script>
    </body>
    </html>
    """

def get_meme_trade_template(meme_all_candidates):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meme Trade Candidates - LumenBro</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            ::-webkit-scrollbar-track {{
                background: #f1f1f1;
            }}
            ::-webkit-scrollbar-thumb {{
                background: #4CAF50;
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: #45a049;
            }}
            .truncate {{
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                cursor: pointer;
            }}
            .expanded {{
                white-space: normal;
                overflow: visible;
                text-overflow: clip;
            }}
            th, td {{
                padding: 8px 12px;
                font-size: 0.875rem;
                word-break: break-word;
            }}
            @media (max-width: 640px) {{
                .hide-on-mobile {{
                    display: none;
                }}
                th, td {{
                    padding: 6px 8px;
                    font-size: 0.75rem;
                }}
            }}
        </style>
    </head>
    <body class="bg-gray-100 font-sans">
        <div class="container mx-auto px-4 py-6">
            <h1 class="text-2xl font-bold text-center text-gray-800 mb-6">Meme Trade Candidates (lu.meme)</h1>
            <div class="overflow-x-auto shadow-lg rounded-lg">
                <table id="candidates-table" class="min-w-full bg-white border border-gray-200">
                    <thead>
                        <tr class="bg-green-500 text-white">
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="source_account">Source Account</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="num_swaps">Num Swaps</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="daily_swaps">Daily Swaps</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="net_xlm_flow">Net XLM Flow</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold hide-on-mobile">Assets Traded</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer" data-sort="score">Score</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold cursor-pointer hide-on-mobile" data-sort="risk_level">Risk Level</th>
                            <th class="py-2 px-3 text-left text-xs font-semibold">Recommendation</th>
                        </tr>
                    </thead>
                    <tbody id="candidates-body" class="text-gray-700"></tbody>
                </table>
            </div>
        </div>

        <script>
            const candidates = {json.dumps(meme_all_candidates)};
            const tbody = document.getElementById('candidates-body');
            candidates.forEach(candidate => {{
                const assetsTraded = Object.entries(candidate.assets_traded).map(([asset, data]) => 
                    `${{asset}}: ${{data.num_swaps}} swaps, In: ${{data.xlm_inflows.toFixed(2)}}, Out: ${{data.xlm_outflows.toFixed(2)}}`
                ).join('\\n');
                const row = document.createElement('tr');
                row.className = 'border-t border-gray-200 hover:bg-gray-50';
                row.innerHTML = `
                    <td class="py-2 px-3 text-xs truncate max-w-[150px]" onclick="this.classList.toggle('expanded')">${{candidate.source_account}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.num_swaps}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.daily_swaps.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.net_xlm_flow.toFixed(2)}}</td>
                    <td class="py-2 px-3 text-xs hide-on-mobile">${{assetsTraded}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.score.toFixed(4)}}</td>
                    <td class="py-2 px-3 text-xs hide-on-mobile">${{candidate.risk_level}}</td>
                    <td class="py-2 px-3 text-xs">${{candidate.recommendation}}</td>
                `;
                tbody.appendChild(row);
            }});

            document.querySelectorAll('th').forEach(header => {{
                header.addEventListener('click', () => {{
                    const table = header.closest('table');
                    const tbody = table.querySelector('tbody');
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    const sortKey = header.getAttribute('data-sort');
                    const isNumeric = ['num_swaps', 'daily_swaps', 'net_xlm_flow', 'score'].includes(sortKey);
                    if (!sortKey) return;

                    const direction = header.classList.contains('sort-asc') ? -1 : 1;
                    document.querySelectorAll('th').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
                    header.classList.add(direction === 1 ? 'sort-asc' : 'sort-desc');

                    rows.sort((a, b) => {{
                        let aValue, bValue;
                        switch (sortKey) {{
                            case 'source_account': aValue = a.cells[0].textContent; bValue = b.cells[0].textContent; break;
                            case 'num_swaps': aValue = parseInt(a.cells[1].textContent); bValue = parseInt(a.cells[1].textContent); break;
                            case 'daily_swaps': aValue = parseFloat(a.cells[2].textContent); bValue = parseFloat(a.cells[2].textContent); break;
                            case 'net_xlm_flow': aValue = parseFloat(a.cells[3].textContent); bValue = parseFloat(a.cells[3].textContent); break;
                            case 'score': aValue = parseFloat(a.cells[5].textContent); bValue = parseFloat(a.cells[5].textContent); break;
                            case 'risk_level': aValue = a.cells[6].textContent; bValue = b.cells[6].textContent; break;
                        }}
                        if (isNumeric) {{
                            return (bValue - aValue) * direction;
                        }} else {{
                            return aValue.localeCompare(bValue) * direction;
                        }}
                    }});

                    while (tbody.firstChild) {{
                        tbody.removeChild(tbody.firstChild);
                    }}
                    rows.forEach(row => tbody.appendChild(row));
                }});
            }});
        </script>
    </body>
    </html>
    """

def get_landing_page_template():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LumenBro Rankings</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 font-sans">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-3xl font-bold text-center text-gray-800 mb-4">Welcome to LumenBro Rankings</h1>
            <p class="text-center text-gray-600 mb-6 max-w-2xl mx-auto">
                Discover top-performing wallets on the Stellar network to enhance your copy trading strategy. 
                Our rankings analyze wallet activity to highlight potential candidates based on metrics like XLM flow, swap frequency, and more.
            </p>
            <p class="text-center text-gray-600 mb-6 max-w-2xl mx-auto">
                <strong>Work in Progress:</strong> These rankings are a proof of concept, and data accuracy is not guaranteed. 
                Use at your own risk, and always conduct your own research before copy trading.
            </p>
            <p class="text-center text-gray-600 mb-8">
                Have questions or feedback? Contact us at 
                <a href="mailto:info@lumenbro.com" class="text-green-500 hover:underline">info@lumenbro.com</a>.
            </p>
            <div class="flex flex-col items-center space-y-4">
                <a href="/webapp" class="w-full max-w-xs py-3 px-4 bg-green-500 text-white text-center rounded-lg hover:bg-green-600 transition duration-300">View Copy Trade Candidates</a>
                <a href="/domain_rankings" class="w-full max-w-xs py-3 px-4 bg-green-500 text-white text-center rounded-lg hover:bg-green-600 transition duration-300">View Domain Rankings (lu.meme)</a>
                <a href="/meme_trade_candidates" class="w-full max-w-xs py-3 px-4 bg-green-500 text-white text-center rounded-lg hover:bg-green-600 transition duration-300">View Meme Trade Candidates (lu.meme)</a>
            </div>
        </div>
    </body>
    </html>
    """
