// my_reports.js

document.addEventListener('DOMContentLoaded', function() {
    const linkReportsButton = document.getElementById("linkReports");

    // Инициализируем фильтрацию отчетов по типу при изменении фильтра. 
    document.getElementById('filter_type').addEventListener('change', function() {
        filterReportsByType();
    });
    

    // Инициализирую слушатель кнопки удалить отчет
    document.querySelectorAll('.my-report-list__button--delete').forEach(button => {
        button.addEventListener('click', deleteReport);
    });

    
});



//Функции


// Фильтрует список протоколов по их типу.
function filterReportsByType() {
    reportTypeSelect = document.getElementById('filter_type');
    existingReportList = document.getElementById('myReportList');
    const selectedType = reportTypeSelect.value;  // Получаем выбранный тип
    const reports = existingReportList.querySelectorAll("li, .my-report-list__item");  // Получаем все протоколы

    reports.forEach(report => {
        const reportType = report.getAttribute("data-report-type");  // Получаем тип отчета
       
        // Если выбран тип "" (All) или тип совпадает с атрибутом отчета, показываем его
        if (selectedType === "" || reportType === selectedType) {
            report.style.display = "flex";  
        } else {
            report.style.display = "none";  // Скрываем отчет, если тип не совпадает
        }
    });
    
}


// Функция удаления отчета
function deleteReport(event){
    button = event.currentTarget;
    const reportId = button.dataset.reportId;
    if (!reportId) {
        console.error('report ID is missing.');
        return;
    }
    
    const confirmation = confirm('Вы действительно хотите удалить протокол? Это действие нельзя отменить.');
    if (!confirmation) return;

        sendRequest({
            url: `/my_reports/delete_report/${reportId}`,
            method: "DELETE",
            csrfToken: csrfToken
        }).then(response => {
            window.location.reload();
        }).catch(error => {
            console.log("Ошибка удаления удаления отчета.");
        });
};




