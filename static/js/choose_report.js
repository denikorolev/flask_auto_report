// choose_report.js


// Логика обновления подтипов в зависимости от выбранного типа
document.addEventListener("DOMContentLoaded", function () {
    
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
    
    // Далее идет формирование тип\подтип списков
    // Чтение данных из скрытого тега <script>
    const reportTypesDataScript = document.getElementById("report-types-data");
    const reportTypesAndSubtypes = JSON.parse(reportTypesDataScript.textContent);

    const reportTypeSelect = document.getElementById("report_type");
    const reportSubtypeSelect = document.getElementById("report_subtype");
    const allSubtypes = {};

    // Проходим по каждому типу и сохраняем его подтипы
    reportTypesAndSubtypes.forEach(type => {
        allSubtypes[type.type_id] = type.subtypes;
    });

    // Функция для обновления подтипов на основе выбранного типа
    function updateSubtypes() {
        const selectedTypeId = reportTypeSelect.value.trim(); // Убедитесь, что значение без пробелов
        reportSubtypeSelect.innerHTML = ''; // Очистить текущие опции

        const subtypes = allSubtypes[selectedTypeId] || [];

        subtypes.forEach(subtype => {
            const option = document.createElement("option");
            option.value = subtype.subtype_id;
            option.textContent = subtype.subtype_text;
            reportSubtypeSelect.appendChild(option);
        });

        // Установить первую опцию как выбранную, если есть подтипы
        if (subtypes.length > 0) {
            reportSubtypeSelect.selectedIndex = 0;
        }
    }

    // Добавление обработчика события для изменения типа
    reportTypeSelect.addEventListener("change", updateSubtypes);

    // Вызов функции для установки начального состояния при загрузке страницы
    updateSubtypes();
});


// Логика нажатия на кнопку получить отчеты, обработки имени фамилии и тд
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

                // Собираем данные формы
                let surname = document.getElementById("patient-surname").value.trim();
                let name = document.getElementById("patient-name").value.trim();
                let patronymic = document.getElementById("patient-patronymicname").value.trim();
                const birthdate = document.getElementById("patient-birthdate").value;
                const reportNumber = document.getElementById("report-number").value;

                // Форматируем ФИО
                surname = surname.charAt(0).toUpperCase() + surname.slice(1).toLowerCase();
                name = name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
                patronymic = patronymic.charAt(0).toUpperCase() + patronymic.slice(1).toLowerCase();

                const fullname = `${surname} ${name} ${patronymic}`;
                const reportId = this.getAttribute("data-report-id");

                // Отправляем данные на сервер через sendRequest
                sendRequest({
                    url: "/working_with_reports/working_with_reports",
                    method: "POST",
                    data: {
                        fullname,
                        birthdate,
                        reportNumber,
                        reportId
                    }
                })
                .then(data => {
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        alert("Failed to prepare report.");
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                });
            });
        });
    }

    // Обработка нажатия на кнопку "Show reports"
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
            }
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
