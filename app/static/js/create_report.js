// create_report.js

import { setupDynamicsDropZone, handleFileUpload, handlePasteFromClipboard } from "/static/js/utils/dynamicsDropZone.js";
import { prepareTextWithAI } from "/static/js/utils/ai_handlers.js";
import { pollTaskStatus, updateProgressBar } from "/static/js/utils/utils_module.js";      

// Массив для хранения последовательности выбора отчетов
let selectedReports = [];
let detachCurrentFilter = null; // Переменная для хранения функции фильтрации отчетов


document.addEventListener("DOMContentLoaded", function() {
    
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
    

});


//Фильтрует подтипы в зависимости от выбранного типа.
function handleReportModalityChange() {
    const modality = parseInt(document.getElementById("reportModality").value, 10); // приводим к числу   
    const reportAreas = document.getElementById("reportArea");

    reportAreas.innerHTML = ''; // Очищаем select

    // Получаем подтипы для выбранного типа
    const selectedModality = Array.isArray(categories)
        ? categories.find(t => Number(t.id) === Number(modality))
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
        return;
    }

    // Добавляем новые options
    currentAreas.forEach(area => {
        const option = document.createElement("option");
        option.value = area.id;
        option.textContent = area.name;
        reportAreas.appendChild(option);
    });
    
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

    // Показываем выбранный
    if (selectedAction === "file") {
        fileUploadContainer.style.display = "flex";
        activateUniversalSearch(); 
    } else if (selectedAction === "manual") {
        manualReportContainer.style.display = "flex";
        activateUniversalSearch(); 
    } else if (selectedAction === "existing_few") {
        existingReportContainer.style.display = "block";
        loadExistingReports();  
    } else if (selectedAction === "shared") {
        sharedReportContainer.style.display = "block";
        loadSharedReports();  
    } else if (selectedAction === "public") {
        publicReportContainer.style.display = "block";
        loadPublicReports();  
    } else if (selectedAction === "ai_generator") {
        aiGeneratorContainer.style.display = "block";
        document.getElementById("Textarea").value = "";
        document.getElementById("DropZonePreview").innerHTML = "";
        activateUniversalSearch();
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
    return {
        modalityID: select.value,
        modalityName: option.getAttribute("data-modality-name"),
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

    try {
        const response = await sendRequest({
            method: "GET",
            url: `/new_report_creation/get_existing_reports?modality_id=${modalityID}`,
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

    try {
        const response = await sendRequest({
            url: `/new_report_creation/get_shared_reports?modality_name=${encodeURIComponent(modalityName)}`,
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
                        ${report.report_name} - ${report.modality}  (${report.shared_by_email})
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

    try {
        const response = await sendRequest({
            method: "GET",
            url: `/new_report_creation/get_public_reports?modality_name=${encodeURIComponent(modalityName)}`
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




// Обработчик для блока ИИ-генерации шаблона
function showAiGeneratorBlock() {
    const container = document.getElementById("aiGeneratorContainer");
    if (!container) {
        console.error("aiGeneratorContainer not found");
        return;
    }

    // Элементы
    const textarea = document.getElementById("Textarea");
    const dropZone = document.getElementById("DropZone");
    const preview = document.getElementById("DropZonePreview");
    const pasteButton = document.getElementById("aiGeneratorPasteButton");
    const uploadBtn = document.getElementById("aiGeneratorUploadButton");
    const prepareButton = document.getElementById("aiGeneratorPrepareButton");
    const cancelButton = document.getElementById("aiGeneratorCancelButton");
    const fileInput = document.getElementById("aiGeneratorFileInput");
    const generateTemplateButton = document.getElementById("aiGeneratorGenerateButton");
    const pollingAbortController = new AbortController(); // Контроллер для отмены запросов
    // Для будущей загрузки файлов с input (пока не реализовано)
    // const fileInput = document.getElementById("aiGeneratorFileInput");

    // Очистка состояния перед показом
    textarea.value = "";
    preview.innerHTML = "";

    // Показываем сам блок (если скрыт)
    container.style.display = "block";

    // Навешиваем MutationObserver
    const observer = new MutationObserver(() => {
        const style = window.getComputedStyle(container);
        if (style.display === "none") {
            detachHandlers();
            observer.disconnect();
            console.log("aiGeneratorContainer скрыт — сняты обработчики");
        }
    });

    // Инициализация dropzone (detach функция для снятия обработчиков)
    let detachDropZone = setupDynamicsDropZone({
        dropZoneId: "DropZone",
        previewId: "DropZonePreview",
        textareaId: "Textarea"
    });

    // Внутренняя функция, нужна чтобы не вводить каждый раз параметры 
    // bar, label, text для универсальной функции updateProgressBar
    function updateDynamicsProgressBar(percent, statusText = null) {
        const progressBarContainer = document.getElementById("dynamicsProgressBarContainer");
        if (progressBarContainer && progressBarContainer.style.display === "none") {
            progressBarContainer.style.display = "block";
        }
        updateProgressBar(
            {
                bar: "dynamicsProgressBar",
                label: "dynamicsProgressBarLabel",
                text: "dynamicsProgressBarText"
            },
            percent,
            statusText
        );
    }

    // Снятие обработчиков
    function detachHandlers() {
        pasteButton.removeEventListener("click", pasteHandler);
        prepareButton.removeEventListener("click", prepareTextHandler);
        cancelButton.removeEventListener("click", cancelHandler);
        fileInput.removeEventListener("change", fileSelectHandler);
        uploadBtn.removeEventListener("click", uploadBtnHandler);
        generateTemplateButton.removeEventListener("click", generateTemplateHandler);
        if (detachDropZone) detachDropZone();
    }


    // Обработчик для вставки текста из буфера обмена
    const pasteHandler = async () => {
        await handlePasteFromClipboard(textarea, preview);
    };

    // Обработчик для кнопки генерации шаблона при помощи ИИ
    const generateTemplateHandler = async () => {
        const rawText = textarea.value.trim();
        const templateName = document.getElementById("reportName").value.trim();
        const templateModality = document.getElementById("reportModality").value;
        const templateSubtype = document.getElementById("reportArea").value;


        if (!rawText) {
            alert("Пожалуйста, введите текст для анализа.");
            return;
        }
        // Блокируем кнопку анализа
        generateTemplateButton.disabled = true;

        const startResponse = await sendRequest({
            url: "/new_report_creation/ai_generate_template",
            data: {
                origin_text: rawText,
                template_name: templateName,
                template_type: templateModality,
                template_subtype: templateSubtype
            }
        });
        const {status, message, task_id} = startResponse || {};
        if (status !== "success" || !task_id) {
            console.error("Ошибка при отправке текста на анализ динамики:", message);
            return;
        }
        
        pollTaskStatus(task_id, {
            maxAttempts: 20,
            interval: 7000,
            onProgress: (progress) => updateDynamicsProgressBar(progress, "Ожидание результата..."),
            onSuccess: (result) => {
                updateDynamicsProgressBar(100, "Готово!");
                alert("Шаблон успешно сгенерирован!");
            },
            onError: (errMsg) => updateDynamicsProgressBar(100, errMsg),
            onTimeout: () => updateDynamicsProgressBar(100, "Превышено время ожидания ответа. Попробуйте ещё раз позже."),
            abortController: pollingAbortController // Передаем контроллер для отмены
            
        });

    };

    // Обработчик "Подготовить текст" — просто вызывает уже существующую функцию
    const prepareTextHandler = async () => {

        const taskID = await prepareTextWithAI(textarea, prepareButton);
        console.log("Task ID:", taskID);
        pollTaskStatus(taskID, {
            maxAttempts: 12,
            interval: 4000,
            onProgress: (progress) => updateDynamicsProgressBar(progress, "Ожидание результата..."),
            onSuccess: (result) => {
                updateDynamicsProgressBar(100, "Готово!");
                textarea.value = result || "";
            },
            onError: (errMsg) => updateDynamicsProgressBar(100, errMsg),
            onTimeout: () => updateDynamicsProgressBar(100, "Превышено время ожидания ответа. Попробуйте ещё раз позже."),
            abortController: pollingAbortController // Передаем контроллер для отмены
        });
    };

    // Заглушка для "Отменить" (можно будет заменить на сброс блока/скрытие)
    const cancelHandler = () => {
        pollingAbortController.abort(); // 💥 Прерывает опрос
    };

    // Обработчик выбора файла
    const fileSelectHandler = (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
            handleFileUpload(file, preview, textarea);
        }
        // Сброс значения чтобы можно было выбрать тот же файл снова при необходимости
        fileInput.value = "";
    };

    // Промежуточный обработчик симулирующий клик на input для 
    // загрузки файла при клике на кнопку загрузить файл
    const uploadBtnHandler = () => {
        fileInput.click();
    };

    // Вешаем обработчики
    pasteButton.addEventListener("click", pasteHandler);
    prepareButton.addEventListener("click", prepareTextHandler);
    cancelButton.addEventListener("click", cancelHandler);
    fileInput.addEventListener("change", fileSelectHandler);
    uploadBtn.addEventListener("click", uploadBtnHandler);
    generateTemplateButton.addEventListener("click", generateTemplateHandler);

    observer.observe(container, { attributes: true, attributeFilter: ["style"] });

    // Вернуть функцию для снятия обработчиков если нужно внести контроль снаружи
    // return () => {
    //     pasteButton.removeEventListener("click", pasteHandler);
    //     prepareButton.removeEventListener("click", prepareTextHandler);
    //     cancelButton.removeEventListener("click", cancelHandler);
    //     if (detachDropZone) detachDropZone();
    // };
}



// Функции для создания отчета после нажатия на кнопку "Создать протокол"

/**
 * Создание протокола вручную с валидацией
 */
function createManualReport() {
    const reportName = document.getElementById("reportName")?.value?.trim();
    const reportSubtype = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";

    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }

    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
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
    const reportSubtype = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
    const reportFile = document.getElementById("report_file")?.files[0];

    // Валидация обязательных полей
    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
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
    formData.append("report_subtype", reportSubtype);
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



// Создание протокола на основе нескольких существующих с валидацией
function createReportFromExistingFew() {
    const reportName = document.getElementById("reportName")?.value?.trim();
    const reportSubtype = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";


    if (selectedReports.length === 0) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }


    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
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
    const reportSubtype = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
    const selectedReportId = document.querySelector("input[name='public_report_radio']:checked").value;
    

    if (!selectedReportId) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }
    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
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

// Создание протокола на протоколов, которые были поделены с пользователем
function createReportFromShared() {
    const reportName = document.getElementById("reportName")?.value?.trim();
    const reportSubtype = document.getElementById("reportArea")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
    const selectedReport = document.querySelector("input[name='shared_report_radio']:checked");
    const selectedReportId = selectedReport?.value;

    if (!selectedReportId) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }
    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
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









