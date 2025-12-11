// Embalagens - Módulo de gestão de estoque

async function carregarEmbalagens() {
    showLoading('embalagens');
    
    try {
        const dados = await api('/api/embalagens');
        
        if (!dados) return;
        
        const grid = document.getElementById('grid_embalagens');
        
        if (dados.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <p class="text-gray-500 italic">
                        Nenhuma embalagem cadastrada. Use o formulário acima para adicionar.
                    </p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = dados.map(e => {
            const isLowStock = e.quantidade < 10;
            const borderColor = isLowStock ? 'border-red-500' : 'border-green-500';
            const stockColor = isLowStock ? 'text-red-600' : 'text-green-600';
            
            return `
                <div class="bg-white p-4 rounded shadow border-l-4 ${borderColor} flex flex-col justify-between group transition-all hover:shadow-md">
                    <div>
                        <h3 class="font-bold text-lg text-gray-800 mb-1">${e.nome}</h3>
                        <p class="text-[10px] text-gray-500 uppercase font-bold">Estoque Atual</p>
                        ${isLowStock ? '<p class="text-xs text-red-500 font-bold">⚠️ ESTOQUE BAIXO</p>' : ''}
                    </div>
                    
                    <!-- Campo de Edição -->
                    <div class="flex items-center gap-2 mt-3 bg-gray-50 p-2 rounded border border-gray-200">
                        <input 
                            type="number" 
                            id="qtd_edit_${e.id}" 
                            value="${e.quantidade}" 
                            min="0"
                            class="w-full bg-transparent font-bold text-xl ${stockColor} outline-none p-1 text-center"
                        >
                        <button 
                            onclick="atualizarEstoqueDireto(${e.id})" 
                            class="bg-blue-600 text-white w-8 h-8 rounded flex items-center justify-center hover:bg-blue-700 shadow transition"
                            title="Salvar Nova Quantidade">
                            <i class="fas fa-save text-xs"></i>
                        </button>
                    </div>
                    
                    <!-- Ações rápidas -->
                    <div class="flex gap-1 mt-2">
                        <button 
                            onclick="ajusteRapido(${e.id}, 10)" 
                            class="flex-1 bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-bold hover:bg-green-200 transition"
                            title="Adicionar 10 unidades">
                            +10
                        </button>
                        <button 
                            onclick="ajusteRapido(${e.id}, -1)" 
                            class="flex-1 bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-bold hover:bg-red-200 transition"
                            title="Remover 1 unidade">
                            -1
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Erro ao carregar embalagens:', error);
    } finally {
        hideLoading('embalagens');
    }
}

async function salvarEmbalagem() {
    const nome = document.getElementById('emb_nome').value.trim();
    const qtd = document.getElementById('emb_qtd').value;
    
    if (!nome || !qtd || parseInt(qtd) <= 0) {
        showNotification('Preencha nome e quantidade válida (> 0).', 'warning');
        return;
    }
    
    try {
        const res = await api('/api/embalagens', 'POST', {
            nome,
            quantidade: parseInt(qtd)
        });
        
        if (!res) return;

        showNotification(res.message, 'success');
        
        // Limpa formulário
        document.getElementById('emb_nome').value = '';
        document.getElementById('emb_qtd').value = '';
        
        // Recarrega listas
        carregarEmbalagens();
        carregarOpcoesEmbalagem();
        
    } catch (error) {
        console.error('Erro ao salvar embalagem:', error);
    }
}

async function atualizarEstoqueDireto(id) {
    const input = document.getElementById(`qtd_edit_${id}`);
    const novoValor = parseInt(input.value);
    
    if (isNaN(novoValor) || novoValor < 0) {
        showNotification('Informe um valor numérico válido (≥ 0).', 'warning');
        return;
    }

    if (confirm('Tem certeza que deseja CORRIGIR o estoque manualmente para este valor?')) {
        try {
            const res = await api('/api/embalagens/editar', 'POST', {
                id: id,
                quantidade: novoValor
            });
            
            if (!res) return;
            
            showNotification(res.message, 'success');
            
            // Recarrega listas
            carregarEmbalagens();
            carregarOpcoesEmbalagem();
            
        } catch (error) {
            console.error('Erro ao atualizar estoque:', error);
        }
    }
}

async function ajusteRapido(id, ajuste) {
    const input = document.getElementById(`qtd_edit_${id}`);
    const valorAtual = parseInt(input.value) || 0;
    const novoValor = Math.max(0, valorAtual + ajuste);
    
    input.value = novoValor;
    
    // Aplica automaticamente
    try {
        const res = await api('/api/embalagens/editar', 'POST', {
            id: id,
            quantidade: novoValor
        });
        
        if (!res) return;
        
        // Feedback visual rápido
        const button = event.target;
        const originalText = button.innerText;
        button.innerText = '✓';
        button.classList.add('bg-green-500', 'text-white');
        
        setTimeout(() => {
            button.innerText = originalText;
            button.classList.remove('bg-green-500', 'text-white');
        }, 1000);
        
        // Recarrega apenas se necessário (para atualizar cores de alerta)
        if (novoValor < 10 || valorAtual < 10) {
            carregarEmbalagens();
        }
        
    } catch (error) {
        console.error('Erro no ajuste rápido:', error);
        input.value = valorAtual; // Reverte
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Formulário de embalagem
    const embalagemForm = document.querySelector('#embalagens .bg-white');
    if (embalagemForm) {
        const saveButton = embalagemForm.querySelector('button');
        if (saveButton) {
            saveButton.addEventListener('click', salvarEmbalagem);
        }
        
        // Enter para salvar
        const inputs = embalagemForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    salvarEmbalagem();
                }
            });
        });
    }
});

// Exportar funções
window.carregarEmbalagens = carregarEmbalagens;
window.salvarEmbalagem = salvarEmbalagem;
window.atualizarEstoqueDireto = atualizarEstoqueDireto;
window.ajusteRapido = ajusteRapido;