// Produtos - Módulo de gestão de produtos

async function carregarProdutos() {
    showLoading('produtos');
    
    try {
        const dados = await api('/api/produtos');
        
        if (!dados) return;
        
        const tbody = document.getElementById('tabela_produtos');
        
        if (dados.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" class="p-4 text-center text-gray-500 italic">
                        Nenhum produto cadastrado.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = dados.map(p => `
            <tr class="hover:bg-gray-50 border-b last:border-0">
                <td class="p-4 font-semibold text-gray-700">${p.nome}</td>
                <td class="p-4">${formatCurrency(p.preco)}</td>
                <td class="p-4 text-gray-500 text-sm">
                    ${p.nome_embalagem || 'Não vinculado'}
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Erro ao carregar produtos:', error);
    } finally {
        hideLoading('produtos');
    }
}

async function salvarProduto() {
    const nome = document.getElementById('prod_nome').value.trim();
    const preco = document.getElementById('prod_preco').value;
    const id_embalagem = document.getElementById('prod_emb').value || null;
    
    if (!nome || !preco) {
        showNotification('Preencha nome e preço do produto', 'warning');
        return;
    }
    
    const precoNum = parseFloat(preco);
    if (isNaN(precoNum) || precoNum <= 0) {
        showNotification('Preço deve ser um valor válido maior que zero', 'warning');
        return;
    }

    try {
        const res = await api('/api/produtos', 'POST', {
            nome,
            preco: precoNum,
            id_embalagem
        });
        
        if (!res) return;

        showNotification(res.message, 'success');
        
        // Limpa formulário
        document.getElementById('prod_nome').value = '';
        document.getElementById('prod_preco').value = '';
        document.getElementById('prod_emb').value = '';
        
        // Recarrega listas
        carregarProdutos();
        carregarOpcoesProdutos();
        
    } catch (error) {
        console.error('Erro ao salvar produto:', error);
    }
}

async function carregarOpcoesEmbalagem() {
    try {
        const dados = await api('/api/embalagens') || [];
        const sel = document.getElementById('prod_emb');
        
        sel.innerHTML = '<option value="">Nenhuma (Não baixa estoque)</option>' + 
            dados.map(e => `<option value="${e.id}">${e.nome}</option>`).join('');
            
    } catch (error) {
        console.error('Erro ao carregar embalagens:', error);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Formulário de produto
    const produtoForm = document.querySelector('#produtos .bg-white');
    if (produtoForm) {
        const saveButton = produtoForm.querySelector('button');
        if (saveButton) {
            saveButton.addEventListener('click', salvarProduto);
        }
        
        // Enter para salvar
        const inputs = produtoForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    salvarProduto();
                }
            });
        });
    }
});

// Exportar funções
window.carregarProdutos = carregarProdutos;
window.salvarProduto = salvarProduto;
window.carregarOpcoesEmbalagem = carregarOpcoesEmbalagem;