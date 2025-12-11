// Pedidos - Módulo de gestão de pedidos

async function carregarListaPedidos() {
    const dataInicio = document.getElementById('filtro_pedidos_ini').value;
    const dataFim = document.getElementById('filtro_pedidos_fim').value;
    
    let url = '/api/pedidos';
    if (dataInicio && dataFim) {
        url += `?data_inicio=${dataInicio}&data_fim=${dataFim}`;
    }

    showLoading('pedidos');
    
    try {
        const dados = await api(url);
        
        if (!dados) return;

        const tbody = document.getElementById('tabela_historico');
        
        if (dados.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="p-8 text-center text-gray-400 italic">
                        Nenhum pedido encontrado no período selecionado.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = dados.map(p => {
            const dataFormatada = formatDate(p.data_hora);
            const statusClass = p.pagamento === 'A Pagar' ? 'status-pending' : 'status-paid';
            
            return `
                <tr class="hover:bg-orange-50 transition border-b last:border-0">
                    <td class="p-3 font-mono text-xs text-gray-500 font-bold">#${p.id}</td>
                    <td class="p-3 text-sm text-gray-600">${dataFormatada}</td>
                    <td class="p-3 font-bold text-gray-800">${p.cliente}</td>
                    <td class="p-3 text-sm text-gray-500 italic max-w-xs truncate" title="${p.descricao}">
                        ${p.descricao}
                    </td>
                    <td class="p-3 text-sm">
                        <span class="status-badge ${statusClass}">
                            ${p.pagamento}
                        </span>
                    </td>
                    <td class="p-3 text-right text-green-600 font-bold">${formatCurrency(p.total)}</td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Erro ao carregar pedidos:', error);
    } finally {
        hideLoading('pedidos');
    }
}

function limparFiltroPedidos() {
    document.getElementById('filtro_pedidos_ini').value = '';
    document.getElementById('filtro_pedidos_fim').value = '';
    carregarListaPedidos();
}

async function finalizarPedido() {
    if (carrinho.length === 0) {
        showNotification('O carrinho está vazio!', 'warning');
        return;
    }
    
    const cliente = {
        nome: document.getElementById('cli_nome').value,
        endereco: document.getElementById('cli_end').value,
        frete: document.getElementById('cli_frete').value,
        pagamento: document.getElementById('cli_pag').value
    };

    if (!cliente.nome) {
        showNotification('Por favor, informe o nome do cliente.', 'warning');
        return;
    }

    try {
        const res = await api('/api/pedidos', 'POST', { cliente, carrinho });
        
        if (!res) return;
        
        let msg = res.message;
        if (res.avisos && res.avisos.length > 0) {
            msg += "\n\n⚠️ ALERTA DE ESTOQUE:\n" + res.avisos.join('\n');
        }
        
        showNotification(msg, 'success');

        // Limpa o estado local
        carrinho = [];
        renderizarCarrinho();
        limparFormularioCliente();

        // Recarrega dados
        carregarDashboard();
        carregarListaPedidos();
        carregarEmbalagens();
        
    } catch (error) {
        console.error('Erro ao finalizar pedido:', error);
    }
}

function limparFormularioCliente() {
    document.getElementById('cli_nome').value = '';
    document.getElementById('cli_end').value = '';
    document.getElementById('cli_frete').value = '';
    document.getElementById('cli_pag').value = 'Dinheiro';
}

// Exportar funções
window.carregarListaPedidos = carregarListaPedidos;
window.limparFiltroPedidos = limparFiltroPedidos;
window.finalizarPedido = finalizarPedido;