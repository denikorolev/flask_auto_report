// choose_report.js




// Логика обновления подтипов в зависимости от выбранного типа
document.addEventListener("DOMContentLoaded", function () {
    const exportForm = document.getElementById("exportForm");
    if (!exportForm) {
        // Получаем параметры из URL, для заполнения формы с ФИО если мы пришли сюда из working with report
        const urlParams = new URLSearchParams(window.location.search);
        const surname = urlParams.get('patient_surname');
        const name = urlParams.get('patient_name');
        const patronymicname = urlParams.get('patient_patronymicname');
        const birthdate = urlParams.get('patient_birthdate');
        const reportNumber = urlParams.get('report_number');

        // Устанавливаем значения полей, если они переданы
        if (surname) document.getElementById("patient-surname").value = surname;
        if (name) document.getElementById("patient-name").value = name;
        if (patronymicname) document.getElementById("patient-patronymicname").value = patronymicname;
        if (birthdate) document.getElementById("patient-birthdate").value = birthdate;
        if (reportNumber) document.getElementById("report-number").value = reportNumber;
    }
    
    // Инициализируем логику типа и подтипа через utils/utils.js
    initializeSubtypeLogic("report_type", "report_subtype", "report-types-data");
});

/**
 * Инициализирует логику выбора подтипа отчета на основе выбранного типа.
  */
function initializeSubtypeLogic(reportTypeSelectId, reportSubtypeSelectId, subtypesDataScriptId) {
    const subtypesDataScript = document.getElementById(subtypesDataScriptId);
    if (!subtypesDataScript) {
        return;
    }
    const reportTypesAndSubtypes = JSON.parse(subtypesDataScript.textContent);
    const allSubtypes = {};

    // Store subtypes grouped by their type_id
    reportTypesAndSubtypes.forEach(type => {
        allSubtypes[type.type_id] = type.subtypes;
    });

    const reportTypeSelect = document.getElementById(reportTypeSelectId);

    if (!reportTypeSelect) {
        return;
    }

    reportTypeSelect.addEventListener("change", function() {
        updateSubtypes(reportTypeSelectId, reportSubtypeSelectId, allSubtypes);
    });

    // Initial update of subtypes
    updateSubtypes(reportTypeSelectId, reportSubtypeSelectId, allSubtypes);
}


/**
 * Обновляет список подтипов отчета в зависимости от выбранного типа.
*/
function updateSubtypes(reportTypeSelectId, reportSubtypeSelectId, allSubtypes) {
    const reportTypeSelect = document.getElementById(reportTypeSelectId);
    const reportSubtypeSelect = document.getElementById(reportSubtypeSelectId);


    if (!reportTypeSelect || !reportSubtypeSelect) {
        return;
    }

    const selectedTypeId = reportTypeSelect.value.trim();
    reportSubtypeSelect.innerHTML = '';

    const subtypes = allSubtypes[selectedTypeId] || [];

    subtypes.forEach(subtype => {
        const option = document.createElement("option");
        option.value = subtype.subtype_id || subtype.id;
        option.textContent = subtype.subtype_text || subtype.subtype;
        reportSubtypeSelect.appendChild(option);
    });

    if (subtypes.length > 0) {
        reportSubtypeSelect.selectedIndex = 0;
    }
}


// Логика нажатия на кнопку "Протоколы", обработки имени фамилии и тд
document.addEventListener("DOMContentLoaded", function () {
    const reportForm = document.getElementById("reportForm");
    const reportTypeSelect = document.getElementById("report_type");
    const reportSubtypeSelect = document.getElementById("report_subtype");
    const reportsListContainer = document.getElementById("reports-list");

    // Функция для обновления списка отчетов
    function updateReportsList(reports) {
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

                let fullname = "";
                let birthdate = "";
                let reportNumber = "";

                // Проверяем наличие формы exportForm
                const exportForm = document.getElementById("exportForm");
                if (exportForm) {
                    // Собираем данные формы, если она существует
                    const surnameField = document.getElementById("patient-surname");
                    const nameField = document.getElementById("patient-name");
                    const patronymicField = document.getElementById("patient-patronymicname");
                    const birthdateField = document.getElementById("patient-birthdate");
                    const reportNumberField = document.getElementById("report-number");

                    // Получаем значения полей с проверкой на их наличие
                    let surname = surnameField ? surnameField.value.trim() : "";
                    let name = nameField ? nameField.value.trim() : "";
                    let patronymic = patronymicField ? patronymicField.value.trim() : "";
                    birthdate = birthdateField ? birthdateField.value : "";
                    reportNumber = reportNumberField ? reportNumberField.value : "";

                    // Форматируем ФИО, если значения есть
                    surname = surname ? surname.charAt(0).toUpperCase() + surname.slice(1).toLowerCase() : "";
                    name = name ? name.charAt(0).toUpperCase() + name.slice(1).toLowerCase() : "";
                    patronymic = patronymic ? patronymic.charAt(0).toUpperCase() + patronymic.slice(1).toLowerCase() : "";

                    fullname = `${surname} ${name} ${patronymic}`.trim();
                }

                const reportId = this.getAttribute("data-report-id");

                // Формируем URL с параметрами
                const url = `/working_with_reports/working_with_reports?fullname=${encodeURIComponent(fullname)}&birthdate=${encodeURIComponent(birthdate)}&reportNumber=${encodeURIComponent(reportNumber)}&reportId=${reportId}`;
                window.location.href = url;
            });
        });
    }


    // Обработка нажатия на кнопку "Протоколы"
    document.getElementById("select_report_type_subtype").addEventListener("click", function (event) {
        event.preventDefault();

        const reportType = reportTypeSelect.value;
        const reportSubtype = reportSubtypeSelect.value;

        // Отправляем запрос на сервер для получения отчетов через sendRequest
        sendRequest({
            url: "/working_with_reports/choosing_report",
            method: "POST",
            data: {
                report_type: reportType,
                report_subtype: reportSubtype
            },
            csrfToken: csrfToken
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
    });

    // Инициализация начальных событий
    addReportLinkEventListeners();
});

// Устанавливаем фокус на поле "Surname" после загрузки страницы
document.addEventListener("DOMContentLoaded", function() {
    const surnameField = document.getElementById("patient-surname");

    if (surnameField) {
        // Проверяем, что элемент видим
        const isVisible = surnameField.offsetWidth > 0 && surnameField.offsetHeight > 0;

        if (isVisible) {
            surnameField.focus();
        } else {
            console.log("Поле 'patient-surname' существует, но невидимо.");
        }
    } else {
        console.log("Поле 'patient-surname' не найдено на странице.");
    }
});
