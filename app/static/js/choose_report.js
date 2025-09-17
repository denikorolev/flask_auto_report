// choose_report.js

document.addEventListener("DOMContentLoaded", function () {

    // Инициализируем логику типа и подтипа
    initializeCategoryLogic();

    // Обработчик нажатия на кнопку "Протоколы"
     document.getElementById("select_report_type_subtype").addEventListener("click", function (event) {
        event.preventDefault();
        getReportsForSelectedCategory();
    });

});


/**
 * Инициализирует логику выбора подтипа отчета на основе выбранного типа.
  */
function initializeCategoryLogic() {
    console.log("Initializing category logic...");
    const userSettings = window.userSettings || {};
    const categories = Array.isArray(userSettings.CATEGORIES_SETUP) ? userSettings.CATEGORIES_SETUP : [];
    if (!categories.length) {
        console.warn("No categories found in user settings.");
        return;
    }
    // Мапим children по id родителя
    const allAreas = {};
    categories.forEach(cat => {
        allAreas[String(cat.id)] = Array.isArray(cat.children) ? cat.children : [];
    });

    const reportModalitySelect = document.getElementById("reportModality");
    const reportAreaSelect = document.getElementById("reportArea");
    if (!reportModalitySelect || !reportAreaSelect) {
        console.warn("Report modality or area select element not found.");
        return;
    }

    // Перестраховка: если селект пустой — наполним его из userSettings (на случай SSR-обрезок)
    if (!reportModalitySelect.options.length && categories.length) {
        categories.forEach(cat => {
            const opt = document.createElement("option");
            opt.value = cat.id;
            opt.textContent = cat.name;
            reportModalitySelect.appendChild(opt);
        });
    }

    reportModalitySelect.addEventListener("change", function () {
        updateAreasFromCategories(reportModalitySelect, reportAreaSelect, allAreas);
        console.log("Selected modality:", reportModalitySelect.value);
    });

    // Первая инициализация
    updateAreasFromCategories(reportModalitySelect, reportAreaSelect, allAreas);
}


/**
 * Обновляет список подтипов отчета в зависимости от выбранного типа.
*/
function updateAreasFromCategories(reportModalitySelect, reportAreaSelect, allAreas) {
    console.log("start updateAreasFromCategories");
    if (!reportModalitySelect || !reportAreaSelect) return;
    console.log("Updating areas...");
    const selectedModalityId = String(reportModalitySelect.value || "").trim();
    reportAreaSelect.innerHTML = "";

    const areas = allAreas[selectedModalityId] || [];

    areas.forEach(area => {
        const opt = document.createElement("option");
        opt.value = area.id;
        opt.textContent = area.name;
        reportAreaSelect.appendChild(opt);
    });

    if (areas.length) {
        reportAreaSelect.selectedIndex = 0;
    }
}


// Функция для обновления списка отчетов
function updateReportsList(reports) {
    const reportsListContainer = document.getElementById("reportsListContainer") || document.createElement("div");
    reportsListContainer.innerHTML = ''; // Очищаем предыдущие результаты

        if (reports.length > 0) {
            const reportsDiv = document.createElement("div");

            reports.forEach(report => {
                const reportLink = document.createElement("a");
                reportLink.classList.add("flex", "report-link");
                reportLink.setAttribute("href", "#");
                reportLink.setAttribute("data-report-id", report.id);

                const reportText = document.createElement("p");
                reportText.classList.add("report__sentence");
                reportText.textContent = report.report_name;

                reportLink.appendChild(reportText);
                reportsDiv.appendChild(reportLink);
            });

            reportsListContainer.appendChild(reportsDiv);
        } else {
            reportsListContainer.innerHTML = '<p>No reports found.</p>';
        }

        // Повторно добавляем обработчик кликов по новым ссылкам
        addReportLinkEventListeners();
    }


// Функция для обработки кликов по ссылкам отчетов
function addReportLinkEventListeners() {
    document.querySelectorAll(".report-link").forEach(link => {
        link.addEventListener("click", function (event) {
            event.preventDefault(); // Останавливаем стандартное поведение ссылки
            const reportId = this.getAttribute("data-report-id");
            // Формируем URL с параметрами
            const url = `/working_with_reports/working_with_reports?reportId=${reportId}`;
            window.location.href = url;
        });
    });
}


    // Функция для обработки клика на кнопку "Протоколы" и загрузки списка отчетов
function getReportsForSelectedCategory () {
    const areaId = document.getElementById("reportArea").value;
    console.log("Fetching reports for areaId:", areaId);

    // Отправляем запрос на сервер для получения отчетов через sendRequest
    sendRequest({
        url: "/working_with_reports/choosing_report",
        data: {
            report_area: areaId
        },
    })
    .then(data => {
        if (data.reports) {
            updateReportsList(data.reports); // Обновляем список отчетов
        } else {
            console.error("No reports found.");
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });

    // Инициализация начальных событий
    addReportLinkEventListeners();
}


