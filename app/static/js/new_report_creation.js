// create_report.js

import { setupDynamicsDropZone } from "/static/js/utils/dynamicsDropZone.js";
import { prepareTextWithAI } from "/static/js/utils/ai_handlers.js";
import { pollTaskStatus } from "/static/js/utils/utils_module.js";    
import { ProgressBar } from "/static/js/utils/elements.js";  

// Массив для хранения последовательности выбора отчетов
let selectedReports = [];
let detachCurrentFilter = null; // Переменная для хранения функции фильтрации отчетов
let CATEGORIES = []; // Глобальная переменная для хранения категорий
let GLOBALCATEGORIES = []; // Глобальная переменная для хранения глобальных категорий
let aiPollingAbort = null; // отдельный для AI-поллинга (не OCR)

document.addEventListener("DOMContentLoaded", function() {
    
    const userSettings = window.userSettings || {};
    CATEGORIES = Array.isArray(userSettings.CATEGORIES_SETUP) ? userSettings.CATEGORIES_SETUP : [];
    GLOBALCATEGORIES = Array.isArray(globalCategories) ? globalCategories : [];
    if (!CATEGORIES.length) {
        console.warn("No categories found in user settings.");
        return;
    }

    // Вешаем обработчик на изменение типа отчета
    document.getElementById("reportModality").addEventListener("change", handleReportModalityChange);
    // Триггерим для начальной настройки(имитируем нажатие от пользователя, чтобы запустить логику выбора)
    document.getElementById("reportModality").dispatchEvent(new Event("change"));

    // Вешаем обработчик на изменение способа создания отчета
    document.querySelectorAll('input[name="action"]').forEach(radio => {
        radio.addEventListener("change", function () {
            handleActionChange(this.value); // Передаем значение выбранного radio input это будет selectedAction
        });
    });

    // Обработчик кнопки ИИ-генерации
    document.getElementById("aiGeneratorButton")?.addEventListener("click", prepareTextForAiGeneration);


    // Вешаем функцию обработчик на кнопку "Создать протокол"
    document.getElementById("createReportButton")?.addEventListener("click", handleCreateReportClick);
    
    // Вешаем обработчик на реакцию выбора "Создать новую область исследования" или "Создать новую модальность"
    document.getElementById("reportArea").addEventListener("change", function() {
        const modalitySelect = document.getElementById("reportModality");
        const parentCategoryID = modalitySelect.value;
        if (this.value !== "new_area") return;
        handleNewCategoryCreation("area", parentCategoryID);
    });

});


//Фильтрует подтипы в зависимости от выбранного типа.
function handleReportModalityChange() {
    const modality = document.getElementById("reportModality").value; // приводим к числу
    const reportAreas = document.getElementById("reportArea");
    if (modality === "new_modality") {
        // Если выбрано создание новой модальности, задаем для попапа 
        // атрибут data-category-type="modality" и запускаем функцию открытия попапа
        const categoryCreationPopup = document.getElementById("categoryEditPopup");
        if (categoryCreationPopup) {
            const parentCategoryID = null; // Для модальности родитель не нужен
            handleNewCategoryCreation("modality", parentCategoryID);
            return;
        }
    }

    if (isNaN(modality)) {
        console.error("Invalid modality selected:", modality);
        return;
    }

    reportAreas.innerHTML = ''; // Очищаем select

    // Получаем подтипы для выбранного типа
    const selectedModality = CATEGORIES
        ? CATEGORIES.find(t => Number(t.id) === Number(modality))
        : null;
    const currentAreas = (selectedModality && Array.isArray(selectedModality.children))
        ? selectedModality.children
        : [];

    // Если нет подтипов, добавлям заглушку
    if (!currentAreas.length) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "Нет доступных подтипов";
        opt.disabled = true;
        opt.selected = true;
        reportAreas.appendChild(opt);
        // сбрасываем выбор отчетов и чекбоксы (если надо)
        selectedReports = [];
        document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        updateOrderCircles();
        // Добавляем опцию создания новой области исследования
        const newAreaOption = document.createElement("option");
        newAreaOption.value = "new_area";
        newAreaOption.textContent = "Создать новую область исследования";
        reportAreas.appendChild(newAreaOption);
        return;
    }

    // Добавляем новые options
    currentAreas.forEach(area => {
        const option = document.createElement("option");
        option.value = area.id;
        option.textContent = area.name;
        reportAreas.appendChild(option);
    });

    const newAreaOption = document.createElement("option");
    newAreaOption.value = "new_area";
    newAreaOption.textContent = "Создать новую область исследования";
    reportAreas.appendChild(newAreaOption);
    
    // Сбрасываем выбор отчетов и чекбоксы (если надо)
    selectedReports = [];
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    updateOrderCircles();

    // Теперь загружаем с сервера список отчётов нужного типа для каждого режима:
    // existing_few, shared, public — по их контейнерам
    if (document.getElementById("existingReportContainer").style.display === "block") {
        loadExistingReports();
    }
    if (document.getElementById("sharedReportContainer").style.display === "block") {
        loadSharedReports();
    }
    if (document.getElementById("publicReportContainer").style.display === "block") {
        loadPublicReports();
    }

}


// Обработчик выбора значения "Создать новую область исследования" или 
// "Создать новую модальность" при выборе одной из данных опций открывает 
//  popup с id categoryEditPopup для создания новой категории.
function handleNewCategoryCreation(categoryType, parentCategoryID) {
    const categoryCreationPopup = document.getElementById("categoryEditPopup");
    
    if (!categoryCreationPopup) {
        console.error("categoryEditPopup not found");
        return;
    }
    if (categoryType === "area" && !parentCategoryID) {
        console.error("parentCategoryID is required for area");
        return;
    }

    // Настраиваем попап в зависимости от того, что выбрано
    const categoryLevel = (categoryType === "modality") ? 1 : (categoryType === "area" ? 2 : null);
    const deleteCategoryButton = categoryCreationPopup.querySelector("#deleteCategoryBtn");
    const createCategoryButton = categoryCreationPopup.querySelector("#saveCategoryEditBtn");
    const popupTitle = categoryCreationPopup.querySelector("#categoryEditPopupTitle");
    const categoryNameInput = categoryCreationPopup.querySelector("#editCategoryName");
    const globalCategorySelect = categoryCreationPopup.querySelector("#editCategoryGlobal");
    const closeBtn = categoryCreationPopup.querySelector("#closeCategoryEditPopup");

    categoryCreationPopup.style.display = "block";
    deleteCategoryButton.style.display = "none"; // Скрываем кнопку удаления при создании новой категории
    createCategoryButton.textContent = "Создать";
    popupTitle.textContent = (categoryType === "modality") 
        ? "Создать новую модальность" 
        : "Создать новую область исследования";

    // Очищаем инпут и селект
    categoryNameInput.value = "";
    globalCategorySelect.innerHTML = "";
    // Добавляем заглушку в селект глобальных категорий
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "— <выберите глобальную категорию> —";
    placeholder.disabled = true;
    placeholder.selected = true;
    globalCategorySelect.appendChild(placeholder);

    // Заполняем селект глобальных категорий в зависимости от уровня категории
    if (categoryLevel === 1) {
        // Список глобальных МОДАЛЬНОСТЕЙ (уровень 1)
        GLOBALCATEGORIES.forEach(category => {
            const option = document.createElement("option");
            option.value = category.id;
            option.textContent = category.name;
            globalCategorySelect.appendChild(option);
        });
    } else {
        // Ищем глобальную модальность-РОДИТЕЛЯ и берём её children (области)
        const parentModality = CATEGORIES.find(cat => String(cat.id) === String(parentCategoryID));
        const globalCategoryIDForParent = parentModality ? parentModality.global_id : null;
        const parent = GLOBALCATEGORIES.find(cat => String(cat.id) === String(globalCategoryIDForParent));
        const children = Array.isArray(parent?.children) ? parent.children : [];
        if (!children.length) {
            console.warn("No global areas found for modality ID:", globalCategoryIDForParent);
        }
        children.forEach(child => {
            const option = document.createElement("option");
            option.value = child.id;
            option.textContent = child.name;
            globalCategorySelect.appendChild(option);
        });
    }

    

    // Отправка данных на сервер для создания новой категории, маршрут category_create в profile_settings
    createCategoryButton.onclick = async () => {
        const data = {
        name: categoryNameInput.value,
        global_id: globalCategorySelect.value,
        level: categoryLevel,
        parent_id: categoryLevel === 2 ? parentCategoryID : null
    };

        try {
            const response = await sendRequest({
                url: "/profile_settings/category_create",
                data: data,
            });

            if (response.status === "success") {
                window.location.reload(); // Перезагружаем страницу чтобы сбросить выбор
            } else {
                alert("Ошибка при создании категории");
                console.error("Error creating category:", response.message);
            }
        } catch (error) {
            console.error("Error creating category:", error);
        }
    };

    // Слушатель закрытия попапа
    closeBtn.onclick = () => {
        categoryCreationPopup.style.display = "none";
        window.location.reload(); // Перезагружаем страницу чтобы сбросить выбор
    };
}

// Функции обработчики


// Активирует универсальный поиск по отчетам в зависимости от видимого списка
function activateUniversalSearch() {
    // Определяем, какой список сейчас видим
    const searchContainer = document.getElementById("reportSearchContainer");
    if (!searchContainer) return;
    searchContainer.style.display = "none"; // Скрываем контейнер поиска, если он был виден

    const lists = [
        document.getElementById("existingReportList"),
        document.getElementById("sharedReportList"),
        document.getElementById("publicReportList")
    ];

    let activeList = null;
    for (const ul of lists) {
        if (ul && ul.parentElement && ul.parentElement.style.display !== "none") {
            activeList = ul;
            break;
        }
    }
    if (!activeList) return;

    if (searchContainer.style.display === "none") {
        searchContainer.style.display = "block"; // Показываем контейнер поиска
    }

    const items = Array.from(activeList.querySelectorAll("li"));
    const inputSelector = "#reportSearchInput";

    // Снимаем старый фильтр, если был
    if (typeof detachCurrentFilter === "function") {
        detachCurrentFilter();
    }

    // Вешаем фильтр на активный список
    detachCurrentFilter = setupTextFilter(inputSelector, items);
}


/**
 * Обновляет номера в кружках порядка выбора отчетов.
 */
function updateOrderCircles() {
    document.querySelectorAll("#existingReportList li").forEach((item) => {
        const input = item.querySelector("input[type='checkbox']");
        const circle = item.querySelector(".existing-fewreports__order-circle");

        if (input && circle) {
            const indexInArray = selectedReports.indexOf(input.value);

            if (indexInArray !== -1) {
                circle.textContent = indexInArray + 1; // Устанавливаем номер
                circle.style.display = "inline-block"; // Показываем кружок
            } else {
                circle.textContent = "";
                circle.style.display = "none"; // Скрываем кружок
            }
        }
    });
}


// Обрабатывает выбор отчетов, управляет массивом `selectedReports`.
function handleReportSelection(event) {
    const target = event.target;

    if (target.type === "checkbox") {
        const reportId = target.value;

        if (target.checked) {
            if (!selectedReports.includes(reportId)) {
                selectedReports.push(reportId);
            }
        } else {
            selectedReports = selectedReports.filter(id => id !== reportId);
        }

        updateOrderCircles();
    }
}


// Определяет выбранное действие и вызывает соответствующую функцию.
function handleCreateReportClick() {
    const selectedRadio = document.querySelector('input[name="action"]:checked');
    const selectedAction = selectedRadio ? selectedRadio.value : null;

    switch (selectedAction) {
        case "manual":
            createManualReport();
            break;
        case "file":
            createReportFromFile();
            break;
        case "existing_few":
            createReportFromExistingFew();
            break;
        case "shared":
            createReportFromShared();
            break;
        case "public":
            createReportFromPublic();
            break;
        default:
            alert("Пожалуйста, выберите способ создания протокола.");
            console.error("Выбрано неизвестное действие:", selectedAction);
    }
}


// Определяет какое значение выбрано в radio input и настраивает вид окна в зависимости от этого.
function handleActionChange(selectedAction) {
    const fileUploadContainer = document.getElementById("reportCreationForm");
    const existingReportContainer = document.getElementById("existingReportContainer");
    const sharedReportContainer = document.getElementById("sharedReportContainer");
    const publicReportContainer = document.getElementById("publicReportContainer");
    const manualReportContainer = document.getElementById("manualReportCreationContainer");
    const aiGeneratorContainer = document.getElementById("aiGeneratorContainer");
    // Скрываем все
    fileUploadContainer.style.display = "none";
    existingReportContainer.style.display = "none";
    sharedReportContainer.style.display = "none";
    publicReportContainer.style.display = "none";
    manualReportContainer.style.display = "none";
    aiGeneratorContainer.style.display = "none";
    

    function toggleCreateReportButton(show) {
        const createReportButton = document.getElementById("createReportButton");
        if (createReportButton) {
            createReportButton.style.display = show ? "block" : "none";
        }
    }

    // Показываем выбранный
    if (selectedAction === "file") {
        fileUploadContainer.style.display = "flex";
        toggleCreateReportButton(true);
        activateUniversalSearch(); 
    } else if (selectedAction === "manual") {
        manualReportContainer.style.display = "flex";
        toggleCreateReportButton(true);
        activateUniversalSearch(); 
    } else if (selectedAction === "existing_few") {
        existingReportContainer.style.display = "block";
        toggleCreateReportButton(true);
        loadExistingReports();  
    } else if (selectedAction === "shared") {
        sharedReportContainer.style.display = "block";
        toggleCreateReportButton(true);
        loadSharedReports();  
    } else if (selectedAction === "public") {
        publicReportContainer.style.display = "block";
        toggleCreateReportButton(true);
        loadPublicReports();  
    } else if (selectedAction === "ai_generator") {
        aiGeneratorContainer.style.display = "block";
        document.getElementById("DropZoneTextarea").value = "";
        document.getElementById("DropZonePreview").innerHTML = "";
        activateUniversalSearch();
        toggleCreateReportButton(false); // Скрываем кнопку создания отчета, т.к. в этом режиме она не нужна
        showAiGeneratorBlock(); // Показываем блок ИИ-генерации
    }

    // Сброс выбранных отчетов
    selectedReports = [];
    // Сброс состояния всех чекбоксов
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });

    updateOrderCircles();

}


// Получает информацию о выбранном типе отчета (для быстрого закидывания в JSON и переменные)
function getReportModalityInfo() {
    const select = document.getElementById("reportModality");
    const option = select.options[select.selectedIndex];
    const modalityID = select.value;
    const globalModalityID = CATEGORIES.find(cat => String(cat.id) === String(modalityID))?.global_id || null;
    const modalityName = option.getAttribute("data-modality-name");
    return {
        modalityID: modalityID,
        globalModalityID: globalModalityID,
        modalityName: modalityName,
        option,
        select,
    };
}



// Отправляет запрос на сервер для получения данных о существующих отчетах
async function loadExistingReports() {
    const list = document.getElementById("existingReportList");
    list.innerHTML = ""; // Очистить список

    // Получаем выбранный тип

    const { modalityID } = getReportModalityInfo();
    const { globalModalityID } = getReportModalityInfo(); // получаем тип отчета

    if (!modalityID || !globalModalityID) {
        list.innerHTML = `<li>Ошибка: Не выбран тип отчета.</li>`;
        return;
    }

    try {
        const response = await sendRequest({
            method: "GET",
            url: `/new_report_creation/get_existing_reports?modality_id=${modalityID}&global_modality_id=${globalModalityID}`,
        });

        if (response.status !== "success") {
            list.innerHTML = `<li>Ошибка: ${response.message}</li>`;
            return;
        }
        if (!response.reports.length) {
            list.innerHTML = `<li>Нет существующих протоколов выбранного типа.</li>`;
            return;
        }

        // Заполняем список
        response.reports.forEach(report => {
            const li = document.createElement("li");
            li.classList.add("existing-fewreports__item");
            li.innerHTML = `
                <input class="existing-fewreports__input--checkbox" type="checkbox" id="report_${report.id}" name="existing_report_id" value="${report.id}">
                <label class="existing-fewreports__label--checkbox" for="report_${report.id}">${report.report_name}</label>
                <span class="existing-fewreports__order-circle"></span>
            `;
            list.appendChild(li);
        });

        // Вешаем обработчик на чекбоксы существующих отчетов
        list.addEventListener("change", handleReportSelection);

        activateUniversalSearch();

    } catch (error) {
        list.innerHTML = `<li>Не удалось загрузить существующие протоколы.</li>`;
        console.error(error);
    }
}




// Отправляет запрос на сервер для получения данных о существующих shared отчетах
async function loadSharedReports() {
    const list = document.getElementById("sharedReportList");
    list.innerHTML = ""; // очистим

    const { modalityName } = getReportModalityInfo(); // получаем тип отчета
    const { globalModalityID } = getReportModalityInfo(); // получаем тип отчета

    try {
        const response = await sendRequest({
            url: `/new_report_creation/get_shared_reports?global_modality_id=${encodeURIComponent(globalModalityID)}&modality_name=${encodeURIComponent(modalityName)}`,
            method: "GET"
        });

        if (response.status != "error") {
            if (!response.reports.length) {
                list.innerHTML = `<li>Нет доступных протоколов от других пользователей.</li>`;
                return;
            }
            response.reports.forEach(report => {
                const li = document.createElement("li");
                li.classList.add("existing-fewreports__item");
                li.innerHTML = `
                    <label>
                        <input type="radio" name="shared_report_radio" value="${report.id}" />
                        ${report.report_name} - ${report.modality}  (${report.shared_by})
                    </label>
                `;
                list.appendChild(li);
            });

            activateUniversalSearch(); // Активируем универсальный поиск по словам
        } 
    } catch (error) {
        list.innerHTML = `<li>Не удалось загрузить протоколы других пользователей.</li>`;
    }
}


// Отправляет запрос на сервер для получения данных о существующих public отчетах
async function loadPublicReports() {    
    const list = document.getElementById("publicReportList");
    list.innerHTML = ""; // сброс

    const { modalityName } = getReportModalityInfo(); // получаем тип отчета
    const { globalModalityID } = getReportModalityInfo(); // получаем тип отчета

    try {
        const response = await sendRequest({
            method: "GET",
            url: `/new_report_creation/get_public_reports?modality_name=${encodeURIComponent(modalityName)}&global_modality_id=${encodeURIComponent(globalModalityID)}`,
        });

        if (response.status === "success" && !response.reports.length) {
            list.innerHTML = `<li>Нет общедоступных протоколов для данного типа.</li>`;
            return;
        }

        if (response.status === "success") {
            const reportModalitySelect = document.getElementById("reportModality");
            const selectedOption = reportModalitySelect.options[reportModalitySelect.selectedIndex];
            const selectedReportModality = selectedOption.getAttribute("data-modality-name");

            // Заполнение списка протоколов
            response.reports.forEach(report => {
                const li = document.createElement("li");
                li.classList.add("public-reports__item");
                li.innerHTML = `
                    <label>
                        <input type="radio" name="public_report_radio" value="${report.id}">
                        ${report.report_name} - ${report.modality}
                    </label>
                `;
                list.appendChild(li);
            });

            activateUniversalSearch(); // Активируем универсальный поиск по словам

        } 
    } catch (error) {
        list.innerHTML = `<li>Не удалось загрузить общедоступные протоколы.</li>`;
        console.error(error);
    }
}




// Функции для создания отчета после нажатия на кнопку "Создать протокол"

/**
 * Создание протокола вручную с валидацией
 */
function createManualReport() {
    const reportName = document.getElementById("reportName")?.value?.trim();
    const reportArea = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";

    if (!reportName || !reportArea) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }

    const jsonData = {
        report_name: reportName,
        report_area: reportArea,
        comment: comment,
        report_side: reportSide
    };

    sendRequest({
        url: "/new_report_creation/create_manual_report",
        data: jsonData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}


// Создание протокола из файла с валидацией
function createReportFromFile() {
    const reportForm = document.getElementById("reportCreationForm");
    const reportName = document.getElementById("reportName")?.value?.trim();
    const reportArea = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
    const reportFile = document.getElementById("report_file")?.files[0];

    // Валидация обязательных полей
    if (!reportName || !reportArea) {
        alert("Заполните все обязательные поля: название протокола и его область исследования!");
        return;
    }

    // Проверка на загруженный файл
    if (!reportFile) {
        alert("Загрузите файл с протоколом!");
        return;
    }

    // Создаем объект FormData для отправки файла
    const formData = new FormData(reportForm);

    // Добавляем остальные поля вручную
    formData.append("report_name", reportName);
    formData.append("report_area", reportArea);
    formData.append("comment", comment);
    formData.append("report_side", reportSide); // булево значение преобразуется автоматически
    
    sendRequest({
        url: "/new_report_creation/create_report_from_file",
        data: formData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}



// Создание протокола на основе нескольких существующих с валидацией (NEEDS TO BE TESTED)
function createReportFromExistingFew() {
    const reportName = document.getElementById("reportName")?.value?.trim();
    const reportArea = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";


    if (selectedReports.length === 0) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportArea) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }


    const jsonData = {
        report_name: reportName,
        report_area: reportArea,
        comment: comment,
        report_side: reportSide,
        selected_reports: selectedReports
    };

    sendRequest({
        url: "/new_report_creation/create_report_from_existing_few",
        data: jsonData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}



function createReportFromPublic() {
    const reportName = document.getElementById("reportName")?.value?.trim();
    const reportArea = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
    const selectedReportId = document.querySelector("input[name='public_report_radio']:checked")?.value;
    

    if (!selectedReportId) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportArea) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }
    const jsonData = {
        report_name: reportName,
        report_area: reportArea,
        comment: comment,
        report_side: reportSide,
        selected_report_id: selectedReportId
    };
    sendRequest({
        url: "/new_report_creation/create_report_from_public",
        data: jsonData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}

// Создание протокола из протоколов, которые были поделены с пользователем
function createReportFromShared() {
    const reportName = document.getElementById("reportName")?.value?.trim();
    const reportArea = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
    const selectedReport = document.querySelector("input[name='shared_report_radio']:checked");
    const selectedReportId = selectedReport?.value;

    if (!selectedReportId) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportArea) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }
    const jsonData = {
        report_name: reportName,
        report_area: reportArea,
        comment: comment,
        report_side: reportSide,
        selected_report_id: selectedReportId,
    };
    sendRequest({
        url: "/new_report_creation/create_report_from_shared",
        data: jsonData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}


// Обработчик для блока ИИ-генерации шаблона
function showAiGeneratorBlock() {
    const container = document.getElementById("aiGeneratorContainer");
    if (!container) {
        console.error("aiGeneratorContainer not found");
        return;
    }

    // Элементы
    const textarea = document.getElementById("DropZoneTextarea");
    const preview = document.getElementById("DropZonePreview");
    const prepareButton = document.getElementById("aiGeneratorPrepareButton");
    const cancelButton = document.getElementById("aiGeneratorCancelButton");
    const generateTemplateButton = document.getElementById("aiGeneratorGenerateButton");
    
    // Progress bar mount point inside AI generator block (dynamic)
    const progressMount = document.getElementById("aiGeneratorProgressBarContainer");
    if (progressMount) {
        progressMount.innerHTML = "";
    }
    // Инициализация прогресс-бара
    const pb = new ProgressBar().mount(progressMount);
    const destroyPB = (delayMs = 0) => {
        const doDestroy = () => {
            try { pb.destroy(); } catch(_) {}
            if (progressMount) progressMount.style.display = "none";
        };
        if (delayMs > 0) setTimeout(doDestroy, delayMs);
        else doDestroy();
    };

    // Очистка состояния перед показом
    textarea.value = "";
    preview.innerHTML = "";
    container.style.display = "block";

    // Навешиваем MutationObserver
    const observer = new MutationObserver(() => {
        const style = window.getComputedStyle(container);
        if (style.display === "none") {
            detachHandlers();
            observer.disconnect();
        }
    });

    // dropzone берёт на себя: dnd, скрытый input, paste (images) и кнопку «Распознать»
    const { detach } = setupDynamicsDropZone();

    function disableGenerateButtons() {
        generateTemplateButton.disabled = true;
        prepareButton.disabled = true;
    }

    function enableGenerateButtons() {
        generateTemplateButton.disabled = false;
        prepareButton.disabled = false;
    }

    // Снятие обработчиков
    function detachHandlers() {
        prepareButton.removeEventListener("click", prepareTextHandler);
        cancelButton.removeEventListener("click", cancelHandler);
        generateTemplateButton.removeEventListener("click", generateTemplateHandler);
        if (typeof detach === "function") detach();
    }


    // Обработчик для кнопки генерации шаблона при помощи ИИ
    const generateTemplateHandler = async () => {
        const rawText = textarea.value.trim();
        const templateName = document.getElementById("reportName").value.trim();
        const templateModalityID = document.getElementById("reportModality").value;
        const globalTemplateModalityID = document.getElementById("reportModality").selectedOptions[0].getAttribute("data-global-id");
        const templateAreaID = document.getElementById("reportArea").value;
        
        if (!rawText) {
            alert("Пожалуйста, введите текст для анализа.");
            return;
        }
        // Блокируем кнопку анализа
        disableGenerateButtons();

        const data = {
                origin_text: rawText,
                template_name: templateName,
                template_modality_id: templateModalityID,
                template_modality_name: document.getElementById("reportModality").selectedOptions[0].textContent,
                template_area_id: templateAreaID,
                template_area_name: document.getElementById("reportArea").selectedOptions[0].textContent,
                global_template_modality_id: globalTemplateModalityID,
                comment: document.getElementById("reportCreationComment").value.trim() || "",
                report_side: document.querySelector("input[name='report_side']:checked")?.value === "true"
            }


        const startResponse = await sendRequest({
            url: "/new_report_creation/ai_generate_template",
            data: data
        });
        const {status, message, task_id} = startResponse || {};
        if (status !== "success" || !task_id) {
            pb.set(100, message || "Не удалось запустить задачу генерации шаблона.");
            enableGenerateButtons();
            destroyPB(1500);
            return;
        }
        
        if (aiPollingAbort) { try { aiPollingAbort.abort(); } catch(_) {} }
            aiPollingAbort = new AbortController();

        if (progressMount) progressMount.style.display = "block";
        pb.set(0, "Задача генерации шаблона запущена...");

        pollTaskStatus(task_id, {
            maxAttempts: 20,
            interval: 7000,
            onProgress: (progress) => pb.set(progress, "Ожидание результата..."),
            onSuccess: (result) => {
                pb.set(100, "Готово!");
                enableGenerateButtons();
                destroyPB(1000);
                aiPollingAbort = null;
                handleAiGeneratedTemplate(result); // Так как ниже мы указываем флаг exclude_result: true, то в result будет task_id
            },
            onError: (errMsg) => {
                pb.set(100, errMsg || "Ошибка при генерации шаблона.");
                enableGenerateButtons();
                destroyPB(2000);
                aiPollingAbort = null;
            },
            onTimeout: () => {
                pb.set(100, "Превышено время ожидания. Попробуйте ещё раз позже.");
                enableGenerateButtons();
                destroyPB(2000);
                aiPollingAbort = null;
            },
            abortController: aiPollingAbort, // Передаем контроллер для отмены
            excludeResult: true // Не забираем json результата подберем его потом по task_id
        });

    };

    // Обработчик "Подготовить текст" — просто вызывает уже существующую функцию
    const prepareTextHandler = async () => {
        const taskID = await prepareTextWithAI(textarea, prepareButton);
        if (!taskID) return;

        // отменяем прошлый опрос если висит
        if (aiPollingAbort) { try { aiPollingAbort.abort(); } catch(_) {} }
        aiPollingAbort = new AbortController();

        if (progressMount) progressMount.style.display = "block";
        pb.set(0, "Запущена задача очистки текста...");

        pollTaskStatus(taskID, {
            maxAttempts: 12,
            interval: 4000,
            onProgress: (progress) => pb.set(progress, "Ожидание результата..."),
            onSuccess: (result) => {
                pb.set(100, "Готово!");
                textarea.value = result || "";
                enableGenerateButtons();
                destroyPB(1000);
                aiPollingAbort = null;
            },
            onError: (errMsg) => {
                pb.set(100, errMsg);
                enableGenerateButtons();
                destroyPB(2000);
                aiPollingAbort = null;
            },
            onTimeout: () => {
                pb.set(100, "Превышено время ожидания ответа. Попробуйте ещё раз позже.");
                enableGenerateButtons();
                destroyPB(2000);
                aiPollingAbort = null;
            },
            abortController: aiPollingAbort // Передаем контроллер для отмены
        });
    };

    // Заглушка для "Отменить" (можно будет заменить на сброс блока/скрытие)
    const cancelHandler = () => {
        try { aiPollingAbort?.abort(); } catch(_) {}
        aiPollingAbort = null;
        enableGenerateButtons();
        destroyPB(500);
    };


    // Вешаем обработчики
    prepareButton.addEventListener("click", prepareTextHandler);
    cancelButton.addEventListener("click", cancelHandler);
    generateTemplateButton.addEventListener("click", generateTemplateHandler);

    observer.observe(container, { attributes: true, attributeFilter: ["style"] });

}


// Функция для обработки результата ИИ-генерации шаблона (отправляет 
// полученный шаблон в json формате на сервер, для создания протокола)
function handleAiGeneratedTemplate(taskID) {
    const textArea = document.getElementById("DropZoneTextarea");
    if (textArea) {
        textArea.value = ""; // очищаем текстовое поле
    }
    if (!taskID || typeof taskID !== "string") {
        console.error("Invalid AI generated template. taskID:", taskID);
        textArea.innerText = "Ошибка: Не удалось получить сгенерированный шаблон.";
        return;
    }

    // Отправляем запрос на сервер чтобы получить результат по taskID
    // в случае success с сервера переходим на страницу редактирования нового протокола
    // в случае error показываем ошибку в textArea
    sendRequest({
        url: `/new_report_creation/get_ai_generated_template?task_id=${encodeURIComponent(taskID)}`,
    }).then(response => {
        const {status, message, report_id} = response || {};
        if (status === "success" && report_id) {
            // Переходим на страницу редактирования нового протокола
            window.location.href = `/editing_report/edit_report?report_id=${report_id}`;
        } else {
            const errorMsg = message || "Не удалось получить сгенерированный шаблон.";
            console.error("Error getting AI generated template:", errorMsg);
            if (textArea) {
                textArea.value = `Ошибка: ${errorMsg}`;
            }
        }
    });
}



