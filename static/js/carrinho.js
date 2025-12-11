// Carrinho - Módulo de gestão do carrinho de compras

async function carregarOpcoesProdutos() {
    try {
        produtosCache = await api('/api/produtos') || [];
        const sel = document.getElementById('sel_produto');
        
        if (produtosCache.length === 0) {
            sel.innerHTML = '<option value="">Nenhum produto cadastrado.</option>';
            return;
        }
        
        sel.innerHTML = '<option value="">Selecione um produto...</option>' + 
            produtosCache.map((p, index) => 
                `<option value="${index}">${p.nome} - ${formatCurrency(p.preco)}</option>`
            ).join('');
            
    } catch (error) {
        console.error('Erro ao carregar produtos:', error);
    }
}

function adicionarAoCarrinho() {
    const index = document.getElementById('sel_produto').value;
    const qtd = parseInt(document.getElementById('qtd_produto').value);
    
    if (index === "" || isNaN(qtd) || qtd < 1) {
        showNotification("Selecione um produto e informe uma quantidade válida.", 'warning');
        return;
    }

    const prod = produtosCache[index];
    const subtotal = prod.preco * qtd;
    
    // Verifica se o produto já está no carrinho
    const itemExistente = carrinho.find(item => item.id === prod.id);
    
    if (itemExistente) {
        itemExistente.qtd += qtd;
        itemExistente.subtotal = itemExistente.preco * itemExistente.qtd;
    } else {
        carrinho.push({ ...prod, qtd, subtotal });
    }
    
    renderizarCarrinho();
    
    // Limpa seleção
    document.getElementById('sel_produto').value = '';
    document.getElementById('qtd_produto').value = '1';
}

function renderizarCarrinho() {
    const lista = document.getElementById('lista_carrinho');
    
    if (carrinho.length === 0) {
        lista.innerHTML = '<li class="text-gray-400 italic text-center py-8">O carrinho está vazio.</li>';
        document.getElementById('total_display').innerText = formatCurrency(0);
        return;
    }
    
    lista.innerHTML = carrinho.map((item, idx) => `
        <li class="flex justify-between items-center border-b pb-2 pt-2 first:pt-0 border-gray-100">
            <div class="flex-1">
                <div class="flex items-center gap-2">
                    <span class="font-bold text-gray-700">${item.qtd}x</span>
                    <span class="text-gray-800">${item.nome}</span>
                </div>
                <div class="text-xs text-gray-500">
                    ${formatCurrency(item.preco)} cada
                </div>
            </div>
            <div class="flex items-center gap-2">
                <span class="font-bold text-gray-800">${formatCurrency(item.subtotal)}</span>
                <button 
                    onclick="editarQuantidade(${idx})" 
                    class="text-blue-500 hover:bg-blue-50 rounded-full w-6 h-6 flex items-center justify-center transition" 
                    title="Editar quantidade">
                    <i class="fas fa-edit text-xs"></i>
                </button>
                <button 
                    onclick="removerItem(${idx})" 
                    class="text-red-500 hover:bg-red-50 rounded-full w-6 h-6 flex items-center justify-center transition" 
                    title="Remover">
                    <i class="fas fa-times text-xs"></i>
                </button>
            </div>
        </li>
    `).join('');
    
    calcularTotal();
}

function calcularTotal() {
    const frete = parseFloat(document.getElementById('cli_frete').value) || 0;
    const subtotal = carrinho.reduce((acc, item) => acc + item.subtotal, 0);
    const total = subtotal + frete;
    
    document.getElementById('total_display').innerText = formatCurrency(total);
}

function editarQuantidade(idx) {
    const item = carrinho[idx];
    const novaQtd = prompt(`Quantidade para ${item.nome}:`, item.qtd);
    
    if (novaQtd === null) return; // Cancelou
    
    const qtd = parseInt(novaQtd);
    if (isNaN(qtd) || qtd < 1) {
        showNotification('Quantidade inválida!', 'warning');
        return;
    }
    
    item.qtd = qtd;
    item.subtotal = item.preco * qtd;
    renderizarCarrinho();
}

function removerItem(idx) {
    if (confirm('Remover este item do carrinho?')) {
        carrinho.splice(idx, 1);
        renderizarCarrinho();
    }
}

function limparCarrinho() {
    if (carrinho.length === 0) return;
    
    if (confirm('Limpar todo o carrinho?')) {
        carrinho = [];
        renderizarCarrinho();
    }
}

// Event listener para recalcular total quando frete mudar
document.addEventListener('DOMContentLoaded', () => {
    const freteInput = document.getElementById('cli_frete');
    if (freteInput) {
        freteInput.addEventListener('input', calcularTotal);
    }
});

// Exportar funções
window.carregarOpcoesProdutos = carregarOpcoesProdutos;
window.adicionarAoCarrinho = adicionarAoCarrinho;
window.renderizarCarrinho = renderizarCarrinho;
window.editarQuantidade = editarQuantidade;
window.removerItem = removerItem;
window.limparCarrinho = limparCarrinho;