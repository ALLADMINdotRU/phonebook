// Глобальная переменная для хранения оригинальных данных карточек
let originalContactsData = [];

/**
 * Транслитерация английских букв в русские
 * Пример: "bdfyjd" → "иванов"
 */
function transliterateToRussian(text) {
    const translitMap = {
        'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г',
        'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
        'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о',
        'k': 'л', 'l': 'д', ';': 'ж', "'": 'э',
        'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
        ',': 'б', '.': 'ю', '/': '.'
    };
    
    return text.toLowerCase().split('').map(char => 
        translitMap[char] || char
    ).join('');
}



/**
 * Инициализация при загрузке страницы
 * Сохраняем исходные данные карточек
 */
function initializeContacts() {
    const cardsContainer = document.getElementById('contacts-cards-container');
    const contactCards = cardsContainer.querySelectorAll('.contact-card');
    
    // Сохраняем данные каждой карточки
    originalContactsData = Array.from(contactCards).map(card => ({
        html: card.outerHTML,
        name: card.getAttribute('data-name') || '',
        email: card.getAttribute('data-email') || '',
        phone: card.getAttribute('data-phone') || '',
        mobile: card.getAttribute('data-mobile') || '',
        title: card.getAttribute('data-title') || '',
        department: card.getAttribute('data-department') || '',
        organization: card.getAttribute('data-organization') || ''
    }));
}

/**
 * Основная функция фильтрации контактов
 * Динамически перестраивает DOM на основе фильтров
 */
function filterContacts() {
    const searchInput = document.getElementById('searchInput');
    const organizationFilter = document.getElementById('organizationFilter');
    const resultsCounter = document.getElementById('resultsCounter');
    const noResults = document.getElementById('noResults');
    const cardsContainer = document.getElementById('contacts-cards-container');
    
    const searchText = searchInput.value.toLowerCase();
    const organizationValue = organizationFilter.value;
    
    let visibleCount = 0;

    
    
    // Создаем новый контейнер для карточек
    const newContainer = document.createElement('div');
    newContainer.className = 'row';
    newContainer.id = 'contacts-cards-container';
    
    // Фильтруем оригинальные данные
    originalContactsData.forEach(contactData => {
        const transliteratedText = transliterateToRussian(searchText);      // Транслитерируем введенный текст

        const matchesSearch = searchText === '' || 
            contactData.name.toLowerCase().includes(searchText) ||
            contactData.name.toLowerCase().includes(transliteratedText) ||
            contactData.email.toLowerCase().includes(searchText) ||
            contactData.email.toLowerCase().includes(transliteratedText) ||
            contactData.phone.includes(searchText) ||
            contactData.phone.includes(transliteratedText) ||
            contactData.mobile.includes(searchText) ||
            contactData.mobile.includes(transliteratedText) ||
            contactData.title.toLowerCase().includes(searchText) ||
            contactData.title.toLowerCase().includes(transliteratedText) ||
            contactData.department.toLowerCase().includes(searchText) ||
            contactData.department.toLowerCase().includes(transliteratedText) ||
            contactData.organization.toLowerCase().includes(searchText) ||
            contactData.organization.toLowerCase().includes(transliteratedText);
        
        const matchesOrganization = organizationValue === '' || 
            contactData.organization === organizationValue;
        
        // Если карточка подходит под фильтры
        if (matchesSearch && matchesOrganization) {
            // Создаем элемент из сохраненного HTML
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-6 col-lg-4 mb-4';
            colDiv.innerHTML = contactData.html;
            
            newContainer.appendChild(colDiv);
            visibleCount++;
        }
    });
    
    // Заменяем старый контейнер новым
    cardsContainer.parentNode.replaceChild(newContainer, cardsContainer);
    
    // Обновляем UI
    updateUI(visibleCount);
}

/**
 * Обновление интерфейса (счетчик и сообщение)
 */
function updateUI(visibleCount) {
    const resultsCounter = document.getElementById('resultsCounter');
    const noResults = document.getElementById('noResults');
    
    if (resultsCounter) {
        resultsCounter.textContent = `Найдено контактов: ${visibleCount}`;
    }
    
    if (noResults) {
        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

/**
 * Очистка фильтров
 */
function clearFilters() {
    const searchInput = document.getElementById('searchInput');
    const organizationFilter = document.getElementById('organizationFilter');
    
    // Очищаем поля ввода
    searchInput.value = '';
    organizationFilter.value = '';
    
    // Применяем фильтрацию (покажет все карточки)
    filterContacts();
}


/**
 * Добавление обработчиков событий
 */
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const organizationFilter = document.getElementById('organizationFilter');
    const clearButton = document.querySelector('button[onclick="clearFilters()"]');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterContacts);
        searchInput.addEventListener('keyup', filterContacts);
    }
    
    if (organizationFilter) {
        organizationFilter.addEventListener('change', filterContacts);
    }
    
    if (clearButton) {
        // Заменяем inline onclick на современный обработчик
        clearButton.onclick = clearFilters;
    }
}

/**
 * Основная инициализация при загрузке DOM
 */
document.addEventListener('DOMContentLoaded', function() {    
    // Ждем немного чтобы все элементы точно были доступны
    setTimeout(() => {
        initializeContacts();
        setupEventListeners();
        filterContacts(); // Первоначальное отображение
        
    }, 100);
});

// Делаем функции глобальными для использования в HTML
window.filterContacts = filterContacts;
window.clearFilters = clearFilters;
