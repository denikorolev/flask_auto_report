


document.addEventListener("DOMContentLoaded", function() {

    wizardInit();
    wizardBindListeners();

});

// Инициализация мастера
function wizardInit() {
    // Показываем первый шаг
    showWizardStep(1);
    // Можно еще инициализировать прогрессбар, если потребуется
}


function wizardBindListeners() {
    // Далее
    safeOn("to-step-2", "click", () => toStep2Handler());
    safeOn("to-step-3", "click", () => toStep3Handler());
    safeOn("to-step-4", "click", () => toStep4Handler());
    safeOn("to-step-5", "click", () => toStep5Handler());
    // Назад
    safeOn("back-to-1", "click", () => showWizardStep(1));
    safeOn("back-to-2", "click", () => showWizardStep(2));
    safeOn("back-to-3", "click", () => showWizardStep(3));
    safeOn("back-to-4", "click", () => showWizardStep(4));
    // Завершить
    safeOn("finish-wizard", "click", () => finishWizardHandler());
}

// Безопасный addEventListener: не кидает ошибку если элемента нет
function safeOn(id, event, handler) {
    const el = document.getElementById(id);
    if (el) el.addEventListener(event, handler);
}

// Показать нужный шаг, остальные скрыть
function showWizardStep(step) {
    const totalSteps = 5;
    for (let i = 1; i <= totalSteps; i++) {
        const stepDiv = document.getElementById(`step-${i}`);
        if (stepDiv) {
            stepDiv.classList.toggle("hide", i !== step);
        }
    }
    updateProgressBar(step, totalSteps);
}


function updateProgressBar(step, totalSteps) {
    const percent = Math.round((step / totalSteps) * 100);
    const bar = document.querySelector("#wizard-progress .progress-bar");
    if (bar) {
        bar.style.width = percent + "%";
        const label = bar.querySelector(".progress-bar__label");
        if (label) {
            label.textContent = `Шаг ${step} из ${totalSteps}`;
        }
    }
}


// ========== Логика шагов (валидация и переходы) ==========

function toStep2Handler() {
    const name = document.getElementById("profile-name").value.trim();
    if (!name) {
        alert("Пожалуйста, введите имя профиля.");
        return;
    }
    if (name.length < 3 || name.length > 50) {
        alert("Имя профиля должно быть от 3 до 50 символов.");
        return;
    }
    showWizardStep(2);
}

function toStep3Handler() { 
    showWizardStep(3); 
}


function toStep4Handler() { 
    // Получаем выбранные модальности
    const checkedModalityIds = Array.from(document.querySelectorAll('input[name="modalities"]:checked')).map(cb => cb.value);
    renderAreasForModalities(checkedModalityIds);
    showWizardStep(4);
}

// функция для отрисовки областей в зависимости от выбранных модальностей
function renderAreasForModalities(selectedModalityIds) {
    const tree = window.globalModalitiesTree;
    const container = document.getElementById("areasContainer");
    container.innerHTML = ""; // Очищаем

    // Создаём flex row для всех модальностей
    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.flexDirection = "row";
    row.style.gap = "32px"; // Можно настроить расстояние между столбцами

    selectedModalityIds.forEach(modId => {
        const modality = tree.find(m => String(m.id) === String(modId));
        if (modality) {
            // Контейнер для модальности (flex column)
            const modalityCol = document.createElement("div");
            modalityCol.style.display = "flex";
            modalityCol.style.flexDirection = "column";
            modalityCol.style.minWidth = "240px";
            modalityCol.style.marginRight = "10px";

            // Заголовок модальности
            const title = document.createElement("div");
            title.className = "modality-title";
            title.innerText = modality.name;
            modalityCol.appendChild(title);

            // Области (children)
            if (modality.children && modality.children.length) {
                modality.children.forEach(area => {
                    const label = document.createElement("label");
                    label.style.display = "block";
                    label.className = "label";
                    label.style.marginLeft = "10px";
                    label.innerHTML = `<input class="checkbox" type="checkbox" name="area-${modality.id}" value="${area.id}" checked> ${area.name}`;
                    modalityCol.appendChild(label);
                });
            } else {
                const noAreas = document.createElement("div");
                noAreas.className = "no-areas";
                noAreas.style.marginLeft = "10px";
                noAreas.innerText = "Нет доступных областей для этой модальности";
                modalityCol.appendChild(noAreas);
            }
            // Добавляем столбец модальности в строку
            row.appendChild(modalityCol);
        }
    });
    // Вставляем flex-row контейнер в основной контейнер
    container.appendChild(row);
}


function toStep5Handler() { 
    showWizardStep(5); 
}

// Финальная отправка профиля (после всех шагов)
function finishWizardHandler() {
    const name = document.getElementById("profile-name").value.trim();
    const description = document.getElementById("profile-desc").value;
    const is_default = document.getElementById("isDefault").checked;
    const agree = document.getElementById("agreeRules").checked;
    const existingProfileId = document.getElementById("profile-name").getAttribute("data-profile-id");

    // --- ВАЖНО: Собираем выбранные модальности ---
    const selectedModalityIds = Array.from(document.querySelectorAll('input[name="modalities"]:checked')).map(cb => cb.value);

    // --- Собираем выбранные области для каждой модальности ---
    const selectedAreas = {};
    selectedModalityIds.forEach(modId => {
        selectedAreas[modId] = Array.from(document.querySelectorAll(`input[name="area-${modId}"]:checked`)).map(cb => cb.value);
    });

    if (!agree) {
        alert("Если вы хотите продолжить работать с программой, вы должны согласиться с правилами использования.");
        return;
    }

    // Собираем итоговый объект
    const profileData = {
        profile_name: name,
        description: description,
        is_default: is_default,
        modalities: selectedModalityIds,   // массив id
        areas: selectedAreas,               // объект: {modalityId: [areaId, ...], ...}
        existing_profile_id: existingProfileId || null
    };

    sendRequest({
        url: "/profile_settings/create_profile",
        data: profileData
    }).then(response => {
        if (response.status === "success") {
            window.location.href = "/profile_settings/choosing_profile?profile_id=" + response.data;
        }
    }).catch(error => {
        console.error("Failed to create profile:", error);
    });
}