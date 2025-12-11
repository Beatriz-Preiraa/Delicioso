// Delicioso - Sistema de Gestão de Pedidos
// Arquivo principal JavaScript

// --- CONFIGURAÇÃO ---
const API_BASE_URL = 'https://delicioso-34fj.onrender.com';

// --- VARIÁVEIS GLOBAIS ---
let carrinho = [];
let produtosCache = [];

// --- UTILITÁRIOS ---
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('loading');
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('loading');
    }
}

function showNotification(message, type = 'info') {
    // Implementar sistema de notificações toast
    alert(message); // Temporário
}

// --- FETCH API HELPER ---
async function api(url, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        console.error('API Error:', error);
        showNotification(`Erro na API: ${error.message}`, 'error');
        throw error;
    }
}

// --- AUTENTICAÇÃO ---
function renderScreen() {
    const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true';
    const appContainer = document.getElementById('app_container');
    const loginScreen = document.getElementById('login_screen');

    if (isLoggedIn) {
        loginScreen.classList.add('hidden');
        appContainer.classList.remove('hidden');
        document.body.classList.remove('justify-center', 'items-center');
        document.body.classList.add('flex');
        showTab('dashboard');
    } else {
        loginScreen.classList.remove('hidden');
        appContainer.classList.add('hidden');
        document.body.classList.add('justify-center', 'items-center');
        document.body.classList.remove('flex');
    }
}

function handleLogin() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const errorElement = document.getElementById('login_error');

    const VALID_USER = 'admin';
    const VALID_PASS = '1234';

    if (user === VALID_USER && pass === VALID_PASS) {
        sessionStorage.setItem('isLoggedIn', 'true');
        errorElement.style.display = 'none';
        renderScreen();
    } else {
        errorElement.innerText = 'Usuário ou senha incorretos. Tente novamente.';
        errorElement.style.display = 'block';
        document.getElementById('password').value = '';
    }
}

function handleLogout() {
    if (confirm('Tem certeza que deseja sair?')) {
        sessionStorage.removeItem('isLoggedIn');
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        renderScreen();
    }
}

// --- NAVEGAÇÃO ---
function showTab(tabId) {
    // Remove classes ativas
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active-nav'));
    
    // Ativa a aba selecionada
    const activeTab = document.getElementById(tabId);
    if (activeTab) activeTab.classList.add('active');
    
    // Ativa o item do menu
    const menuItems = document.querySelectorAll('.sidebar-item');
    menuItems.forEach(item => {
        if (item.getAttribute('onclick') && item.getAttribute('onclick').includes(tabId)) {
            item.classList.add('active-nav');
        }
    });

    // Fecha menu mobile após seleção
    closeMobileMenu();

    // Carrega dados específicos da aba
    switch (tabId) {
        case 'dashboard':
            carregarDashboard();
            break;
        case 'produtos':
            carregarProdutos();
            carregarOpcoesEmbalagem();
            break;
        case 'embalagens':
            carregarEmbalagens();
            break;
        case 'novo_pedido':
            carregarOpcoesProdutos();
            break;
        case 'pedidos':
            carregarListaPedidos();
            break;
    }
}

// --- MENU MOBILE ---
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile_overlay');
    
    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('active');
}

function closeMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile_overlay');
    
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('active');
}

// --- RESPONSIVIDADE ---
function handleResize() {
    // Fecha menu mobile em telas grandes
    if (window.innerWidth > 640) {
        closeMobileMenu();
    }
    
    // Ajusta layout de tabelas
    adjustTableLayout();
}

function adjustTableLayout() {
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        if (window.innerWidth < 768) {
            table.style.fontSize = '0.875rem';
        } else {
            table.style.fontSize = '';
        }
    });
}

// --- INICIALIZAÇÃO ---
window.addEventListener('DOMContentLoaded', () => {
    renderScreen();
    
    // Event listeners para formulários
    const loginForm = document.querySelector('#login_screen form');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleLogin();
        });
    }
    
    // Event listeners para responsividade
    window.addEventListener('resize', handleResize);
    
    // Touch events para mobile
    setupTouchEvents();
    
    // Ajuste inicial
    handleResize();
});

// --- TOUCH EVENTS ---
function setupTouchEvents() {
    // Swipe para abrir/fechar menu mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    document.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
    
    function handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        const minSwipeDistance = 100;
        
        // Swipe da esquerda para direita (abrir menu)
        if (swipeDistance > minSwipeDistance && touchStartX < 50) {
            if (window.innerWidth <= 640) {
                toggleMobileMenu();
            }
        }
        
        // Swipe da direita para esquerda (fechar menu)
        if (swipeDistance < -minSwipeDistance) {
            closeMobileMenu();
        }
    }
}

// Exportar funções globais para uso nos outros módulos
window.DeliciosoApp = {
    api,
    showTab,
    formatCurrency,
    formatDate,
    showLoading,
    hideLoading,
    showNotification,
    toggleMobileMenu,
    closeMobileMenu
};

// Exportar funções para uso global
window.showTab = showTab;
window.toggleMobileMenu = toggleMobileMenu;
window.closeMobileMenu = closeMobileMenu;
window.handleLogin = handleLogin;
window.handleLogout = handleLogout;