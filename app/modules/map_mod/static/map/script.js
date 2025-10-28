// Основной скрипт для модуля карты
document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('map-container');
    const buildingPlan = document.getElementById('building-plan');
    const userMarkers = document.getElementById('user-markers');
    
    // Инициализация
    initMap();
    initUserList();
    loadExistingMarkers();
    
    // Глобальные переменные для режима размещения
    let placementMode = false;
    let userToPlace = null;
    

    // Инициализация карты
    function initMap() {
        if (!buildingPlan) return;
        
        // Обработчик кликов по карте для размещения пользователей
        buildingPlan.addEventListener('click', function(e) {
            if (!placementMode || !userToPlace) return;
            
            const rect = buildingPlan.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Сохраняем координаты
            saveUserCoordinates(userToPlace.id, `${x},${y}`);
            
            // Выходим из режима размещения
            exitPlacementMode();
        });
        
        // Добавляем функциональность перетаскивания
        initDragAndDrop();
    }
    
    // Функциональность перетаскивания карты
    function initDragAndDrop() {
        let isDragging = false;
        let startX, startY;
        let scrollLeft, scrollTop;

        mapContainer.addEventListener('mousedown', (e) => {
            if (e.button === 0 && !placementMode) { // Левая кнопка и не в режиме размещения
                isDragging = true;
                startX = e.pageX - mapContainer.offsetLeft;
                startY = e.pageY - mapContainer.offsetTop;
                scrollLeft = mapContainer.scrollLeft;
                scrollTop = mapContainer.scrollTop;
                mapContainer.style.cursor = 'grabbing';
                buildingPlan.style.cursor = 'grabbing';
                
                // Предотвращаем выделение текста при перетаскивании
                e.preventDefault();
            }
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                mapContainer.style.cursor = 'grab';
                buildingPlan.style.cursor = 'default';
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging || placementMode) return;
            
            // Перетаскиваем только если левая кнопка зажата
            if (e.buttons !== 1) {
                isDragging = false;
                mapContainer.style.cursor = 'grab';
                buildingPlan.style.cursor = 'default';
                return;
            }
            
            e.preventDefault();
            const x = e.pageX - mapContainer.offsetLeft;
            const y = e.pageY - mapContainer.offsetTop;
            const walkX = (x - startX) * 2;
            const walkY = (y - startY) * 2;
            
            mapContainer.scrollLeft = scrollLeft - walkX;
            mapContainer.scrollTop = scrollTop - walkY;
        });

        // Устанавливаем начальный курсор
        mapContainer.style.cursor = 'grab';
    }
    
    // Активировать режим размещения
    function activatePlacementMode(userId, userName) {
        placementMode = true;
        userToPlace = { id: userId, name: userName };
        
        // Показываем подсказку
        showToast(`Режим размещения: ${userName}. Кликните на карте`, 'info');
        
        // Меняем курсор на указатель размещения
        buildingPlan.style.cursor = 'crosshair';
        mapContainer.style.cursor = 'crosshair';
    }
    
    // Выйти из режима размещения
    function exitPlacementMode() {
        placementMode = false;
        userToPlace = null;
        
        // Возвращаем обычный курсор
        buildingPlan.style.cursor = 'default';
        mapContainer.style.cursor = 'default';
    }
    
    // Инициализация списка пользователей
    function initUserList() {
        const searchInput = document.getElementById('user-search');
        const userItems = document.querySelectorAll('.user-item');
        
        // Поиск пользователей
        searchInput.addEventListener('input', function() {
            const searchText = this.value.toLowerCase();
            
            userItems.forEach(item => {
                const userName = item.querySelector('strong').textContent.toLowerCase();
                const userTitle = item.querySelector('.text-muted').textContent.toLowerCase();
                const userDept = item.querySelector('small:not(.text-muted)').textContent.toLowerCase();
                
                const matches = userName.includes(searchText) || 
                              userTitle.includes(searchText) || 
                              userDept.includes(searchText);
                
                item.style.display = matches ? 'block' : 'none';
            });
        });
        
        // Обработчики кнопок размещения
        document.querySelectorAll('.btn-place').forEach(btn => {
            btn.addEventListener('click', function() {
                const userItem = this.closest('.user-item');
                const userId = userItem.dataset.userId;
                const userName = userItem.querySelector('strong').textContent;
                
                // Активируем режим размещения
                activatePlacementMode(userId, userName);
            });
        });
        
        // Обработчики кнопок поиска
        document.querySelectorAll('.btn-find').forEach(btn => {
            btn.addEventListener('click', function() {
                const userItem = this.closest('.user-item');
                const userId = userItem.dataset.userId;
                findUserOnMap(userId);
            });
        });
        
        // Обработчики кнопок удаления
        document.querySelectorAll('.btn-remove').forEach(btn => {
            btn.addEventListener('click', function() {
                const userItem = this.closest('.user-item');
                const userId = userItem.dataset.userId;
                
                if (confirm('Убрать пользователя с карты?')) {
                    removeUserFromMap(userId);
                }
            });
        });
        
    }
    
    // Загрузка существующих маркеров
    function loadExistingMarkers() {
        const users = document.querySelectorAll('.user-item');
        
        users.forEach(userItem => {
            const userId = userItem.dataset.userId;
            const coordinates = userItem.dataset.coordinates;
            
            if (coordinates) {
                const [x, y] = coordinates.split(',').map(Number);
                createUserMarker(userId, x, y);
            }
        });
    }
    
    // Показать предварительный маркер
    function showPreviewMarker(x, y) {
        // Удаляем старый предварительный маркер
        const oldPreview = document.querySelector('.preview-marker');
        if (oldPreview) oldPreview.remove();
        
        // Создаем новый предварительный маркер
        const marker = document.createElement('div');
        marker.className = 'preview-marker';
        marker.style.cssText = `
            position: absolute;
            left: ${x - 15}px;
            top: ${y - 15}px;
            width: 30px;
            height: 30px;
            background-color: rgba(0, 123, 255, 0.3);
            border: 2px solid #007bff;
            border-radius: 50%;
            cursor: pointer;
            z-index: 1000;
        `;
        
        userMarkers.appendChild(marker);
    }
    
    // Создать маркер пользователя
    function createUserMarker(userId, x, y) {
        const marker = document.createElement('div');
        marker.className = 'user-marker';
        marker.dataset.userId = userId;
        marker.style.cssText = `
            position: absolute;
            left: ${x - 12}px;
            top: ${y - 12}px;
            width: 24px;
            height: 24px;
            background-color: #dc3545;
            border: 2px solid white;
            border-radius: 50%;
            cursor: pointer;
            z-index: 900;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        `;
        
        // Всплывающая подсказка при наведении
        marker.title = 'Кликните для информации';
        
        // Обработчик клика для показа информации
        marker.addEventListener('click', function() {
            showUserInfo(userId);
        });
        
        userMarkers.appendChild(marker);
        return marker;
    }
    
    // Сохранить координаты пользователя
    async function saveUserCoordinates(userId, coordinates) {
        try {
            const url = `/map/update_coordinates/${userId}`;
            console.log('Saving coordinates to:', url);
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ coordinates: coordinates })
            });
            
            console.log('Response status:', response.status, response.statusText);
            
            // Проверяем content-type перед парсингом JSON
            const contentType = response.headers.get('content-type');
            console.log('Content-Type:', contentType);
            
            if (!contentType || !contentType.includes('application/json')) {
                // Читаем текст ответа для отладки
                const text = await response.text();
                console.error('Non-JSON response:', text.substring(0, 200));
                throw new Error(`Сервер вернул HTML вместо JSON. Status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('JSON response:', result);
            
            if (result.success) {
                // Обновляем интерфейс
                updateUserInterface(userId, coordinates);
                showToast('Координаты сохранены', 'success');
            } else {
                showToast('Ошибка сохранения: ' + (result.message || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showToast('Ошибка: ' + error.message, 'error');
        }
    }
    
    // Получить CSRF токен
    function getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
    
    // Убрать пользователя с карты
    async function removeUserFromMap(userId) {
        try {
            const response = await fetch(`/map/remove/${userId}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            // Проверяем content-type перед парсингом JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Сервер вернул не JSON ответ');
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Удаляем маркер и обновляем интерфейс
                removeUserMarker(userId);
                updateUserInterface(userId, null);
                showToast('Пользователь удален с карты', 'success');
            } else {
                showToast('Ошибка удаления', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showToast('Ошибка: ' + error.message, 'error');
        }
    }
        
    // Обновить интерфейс пользователя
    function updateUserInterface(userId, coordinates) {
        const userItem = document.querySelector(`[data-user-id="${userId}"]`);
        if (!userItem) return;
        
        // Обновляем кнопки
        const findBtn = userItem.querySelector('.btn-find');
        const removeBtn = userItem.querySelector('.btn-remove');
        
        if (coordinates) {
            const btnGroup = userItem.querySelector('.btn-group');
            
            // Добавляем кнопку "Найти" если ее нет
            if (!findBtn) {
                const findButton = document.createElement('button');
                findButton.className = 'btn btn-outline-success btn-find btn-sm';
                findButton.title = 'Найти на карте';
                findButton.innerHTML = '<i class="bi bi-search"></i>';
                findButton.addEventListener('click', function() {
                    findUserOnMap(userId);
                });
                btnGroup.appendChild(findButton);
            }
            
            // Добавляем кнопку "Удалить" если ее нет
            if (!removeBtn) {
                const removeButton = document.createElement('button');
                removeButton.className = 'btn btn-outline-danger btn-remove btn-sm';
                removeButton.title = 'Убрать с карты';
                removeButton.innerHTML = '<i class="bi bi-x-circle"></i>';
                removeButton.addEventListener('click', function() {
                    removeUserFromMap(userId);
                });
                btnGroup.appendChild(removeButton);
            }
            
            // Создаем/обновляем маркер
            const [x, y] = coordinates.split(',').map(Number);
            removeUserMarker(userId);
            createUserMarker(userId, x, y);
            
        } else {
            // Удаляем обе кнопки и маркер
            if (findBtn) findBtn.remove();
            if (removeBtn) removeBtn.remove();
            removeUserMarker(userId);
        }
    }

    
    // Найти пользователя на карте
    function findUserOnMap(userId) {
        const marker = document.querySelector(`.user-marker[data-user-id="${userId}"]`);
        if (!marker) return;
        
        // Центрируем карту на маркере
        const markerRect = marker.getBoundingClientRect();
        const containerRect = mapContainer.getBoundingClientRect();
        
        mapContainer.scrollTo({
            left: marker.offsetLeft - containerRect.width / 2 + markerRect.width / 2,
            top: marker.offsetTop - containerRect.height / 2 + markerRect.height / 2,
            behavior: 'smooth'
        });
        
        // Анимация мигания
        blinkMarker(marker);
    }
    
    // Анимация мигания маркера
    function blinkMarker(marker) {
        let count = 0;
        const maxBlinks = 3; // Уменьшим количество до 3 раз
        
        const interval = setInterval(() => {
            // Полностью скрываем маркер
            marker.style.display = 'none';
            
            setTimeout(() => {
                // Показываем маркер обратно
                marker.style.display = 'block';
                count++;
                
                if (count >= maxBlinks) {
                    clearInterval(interval);
                }
            }, 200); // Задержка перед появлением
        }, 400); // Интервал между циклами
    }


    
    // Удалить маркер пользователя
    function removeUserMarker(userId) {
        const marker = document.querySelector(`.user-marker[data-user-id="${userId}"]`);
        if (marker) marker.remove();
    }
    
    // Показать информацию о пользователе
    function showUserInfo(userId) {
        // Здесь можно реализовать всплывающее окно с информацией о пользователе
        console.log('Show info for user:', userId);
    }
    
    // Вспомогательная функция для показа уведомлений
    function showToast(message, type = 'info') {
        // Простая реализация уведомлений
        alert(`${type.toUpperCase()}: ${message}`);
    }
});
