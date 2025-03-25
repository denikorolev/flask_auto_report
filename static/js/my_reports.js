// my_reports.js

document.addEventListener('DOMContentLoaded', function() {

    document.getElementById('filter_type').addEventListener('change', filterReports);
    document.getElementById('reportSearch').addEventListener('input', filterReports);

    
    // Инициализирую слушатель кнопки удалить отчет
    document.querySelectorAll('.my-report-list__button--delete').forEach(button => {
        button.addEventListener('click', deleteReport);
    });

    
});



//Функции

// Филтрует отчеты по типу и тексту
function filterReports() {
    const selectedType = document.getElementById('filter_type').value;
    const searchText = document.getElementById("reportSearch").value.toLowerCase();
    const reports = document.querySelectorAll(".my-report-list__item");

    reports.forEach(report => {
        const reportType = report.getAttribute("data-report-type");

        const subtype = report.querySelector('input[name="report_subtype"]').value.toLowerCase();
        const name = report.querySelector('input[name="report_name"]').value.toLowerCase();
        const comment = report.querySelector('input[name="comment"]').value.toLowerCase();

        const matchType = selectedType === "" || reportType === selectedType;
        const matchText = subtype.includes(searchText) || name.includes(searchText) || comment.includes(searchText);

        report.style.display = (matchType && matchText) ? "flex" : "none";
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




