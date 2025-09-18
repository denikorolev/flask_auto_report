// snapshot.js

document.addEventListener("DOMContentLoaded", function () {

    // Слушатель события для кнопки "Сделать снимок"
    document.getElementById("findSnapshotButton").addEventListener("click", function () {
        findButtonHandler();
        }
    );

});



async function findButtonHandler() {
    const date = document.getElementById("snapshotDate").value;
    const reportModality = document.getElementById("snapshotReportModality").value;
    if (!date || !reportModality) {
        toastr.warning("Укажите дату и тип отчета для поиска");
        return;
    }
    try {
        const response = await sendRequest({
            url: "/snapshots/snapshots_json",
            data: {
                date: date,
                report_modality: reportModality
            },
        });
        document.getElementById("snapshotResults").innerHTML = response.data;
    } catch (error) {
        toastr.error("Ошибка при получении данных");
        console.error("Error:", error);
    }
}