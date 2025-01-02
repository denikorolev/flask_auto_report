// my_reports.js

document.addEventListener('DOMContentLoaded', function() {
    const filterTypeSelect = document.getElementById('filter_type');
    const reportList = document.getElementById('reports_list');
    // Инициализируем фильтрацию отчетов по типу при изменении фильтра
    filterTypeSelect.addEventListener('change', function() {
        filterReportsByType(filterTypeSelect, reportList);
    });

    // Инициализирую слушатель кнопки удалить отчет

});


function deleteReport(button){
    const reportId = button.getAttribute("data-report-id") 
    
    if (!reportId) {
        toastr.error('report ID is missing.');
        return;
    }
    
    const confirmation = confirm('Are you sure you want to delete this report?');
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
