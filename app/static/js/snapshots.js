// snapshot.js

document.addEventListener("DOMContentLoaded", function () {

    // Слушатель события для кнопки "Сделать снимок"
    document.getElementById("findSnapshotButton").addEventListener("click", function () {
        findButtonHandler();
        }
    );

});





async function findButtonHandler() {
    const Date = document.getElementById("snapshotDate").value;
    const reportType = document.getElementById("snapshotReportType").value;
    if (!Date || !reportType) {
        toastr.warning("Укажите дату и тип отчета для поиска");
        return;
    }
    try {
        const response = await sendRequest({
            url: "/working_with_reports/snapshots_json",
            data: {
                date: Date,
                report_type: reportType
            },
        });
        document.getElementById("snapshotResults").innerHTML = response.data;
    } catch (error) {
        toastr.error("Ошибка при получении данных");
        console.error("Error:", error);
    }
}