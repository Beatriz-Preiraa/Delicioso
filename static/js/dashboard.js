// Dashboard - Módulo de métricas e relatórios

async function carregarDashboard() {
    const ini = document.getElementById('dash_data_ini');
    const fim = document.getElementById('dash_data_fim');
    
    // Define data padrão como hoje
    const hoje = new Date().toISOString().split('T')[0];
    if (!ini.value) ini.value = hoje;
    if (!fim.value) fim.value = hoje;
    
    showLoading('dashboard');
    
    try {
        const dados = await api(`/api/dashboard?data_inicio=${ini.value}&data_fim=${fim.value}`);
        
        if (!dados) return;

        // Atualiza métricas principais
        document.getElementById('dash_faturamento').innerText = formatCurrency(dados.faturamento_total);
        document.getElementById('dash_apagar').innerText = formatCurrency(dados.a_pagar_total);
        document.getElementById('dash_frete_alto').innerText = formatCurrency(dados.frete_maior_2);
        document.getElementById('dash_qtd_frete_alto').innerText = `${dados.qtd_frete_maior_2} un`;
        document.getElementById('dash_frete_baixo').innerText = formatCurrency(dados.frete_menor_2);
        document.getElementById('dash_qtd_frete_baixo').innerText = `${dados.qtd_frete_menor_2} un`;

        // Renderiza resumo de pagamentos
        renderizarPagamentos(dados.pagamentos);
        
        // Renderiza lista de devedores
        renderizarDevedores(dados.devedores);
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
    } finally {
        hideLoading('dashboard');
    }
}

function renderizarPagamentos(pagamentos) {
    const listaPag = document.getElementById('lista_pagamentos');
    listaPag.innerHTML = '';
    
    for (const [metodo, valor] of Object.entries(pagamentos)) {
        const iconClass = getPaymentIcon(metodo);
        listaPag.innerHTML += `
            <li class="flex justify-between items-center border-b border-gray-100 pb-2 last:border-0">
                <span class="text-gray-600 flex items-center">
                    <i class="${iconClass} text-gray-400 mr-2 w-4"></i> ${metodo}
                </span>
                <span class="font-bold text-gray-800 bg-gray-100 px-2 py-1 rounded">${formatCurrency(valor)}</span>
            </li>
        `;
    }
}

function renderizarDevedores(devedores) {
    const listaDev = document.getElementById('lista_devedores');
    
    if (devedores.length === 0) {
        listaDev.innerHTML = `
            <tr>
                <td colspan="3" class="p-4 text-center text-gray-400 italic bg-gray-50 rounded">
                    Ninguém devendo neste período.
                </td>
            </tr>
        `;
    } else {
        listaDev.innerHTML = devedores.map(d => `
            <tr class="hover:bg-red-50 transition">
                <td class="px-3 py-2 border-b text-gray-500 text-xs">#${d.id_pedido}</td>
                <td class="px-3 py-2 border-b font-semibold text-gray-700">${d.nome}</td>
                <td class="px-3 py-2 border-b text-right text-red-600 font-bold">${formatCurrency(d.valor)}</td>
            </tr>
        `).join('');
    }
}

function getPaymentIcon(metodo) {
    const icons = {
        'Dinheiro': 'fas fa-money-bill-wave',
        'Pix': 'fas fa-qrcode',
        'Cartão': 'fas fa-credit-card',
        'A Pagar': 'fas fa-clock'
    };
    return icons[metodo] || 'fas fa-money-bill-wave';
}

// Exportar funções
window.carregarDashboard = carregarDashboard;