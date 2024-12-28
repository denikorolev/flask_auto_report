// my_reports.js

document.addEventListener('DOMContentLoaded', function() {
    const filterTypeSelect = document.getElementById('filter_type');
    const reportList = document.getElementById('reports_list');
    console.log("filterTypeSelect:", filterTypeSelect);
    console.log("reportList:", reportList);
    // Инициализируем фильтрацию отчетов по типу при изменении фильтра
    filterTypeSelect.addEventListener('change', function() {
        filterReportsByType(filterTypeSelect, reportList);
    });
});