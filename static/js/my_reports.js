// my_reports.js

document.addEventListener('DOMContentLoaded', function() {
    const filterTypeSelect = document.getElementById('filter_type');
    const reportList = document.getElementById('reports_list');

    // Инициализируем фильтрацию отчетов по типу при изменении фильтра. 
    // Функция filterReportsByType находится в utils.js
    filterTypeSelect.addEventListener('change', function() {
        filterReportsByType(filterTypeSelect, reportList);
    });

    // Инициализирую слушатель кнопки удалить отчет
    document.querySelectorAll('.my-report-list__button--delete').forEach(button => {
        button.addEventListener('click', deleteReport);
    });
});



//Функции

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
