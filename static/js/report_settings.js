// static/js/report_settings.js








// Логика для добавления нового типа параграфа
document.getElementById('paragraph-type-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent form submission and page reload

    const input = document.getElementById('new_paragraph_type');
    const newTypeName = input.value.trim();

    if (!newTypeName) {
        alert('Paragraph type name cannot be empty.');
        return;
    }

    try {
        const response = await sendRequest({
            url: '/report_settings/add_paragraph_type',  // Directly use the URL string
            method: 'POST',
            data: { new_paragraph_type: newTypeName },
        });

        // If the request is successful, update the list on the page
        if (response.status === 'success') {
            const paragraphTypesList = document.getElementById('paragraph-types-list');
            const newListItem = document.createElement('li');
            newListItem.textContent = newTypeName;
            paragraphTypesList.appendChild(newListItem);

            input.value = ''; // Clear the input field
            toastr.success(response.message);
        } else {
            alert(response.message);
        }
    } catch (error) {
        // Handle the error returned by sendRequest
        alert(error.message || 'An error occurred while adding the paragraph type.');
    }
});


// Загрузка файла шаблона для word на сервер
document.getElementById("file-upload-form").addEventListener("submit", function(event) {
    event.preventDefault();
    
    const formData = new FormData();
    const fileInput = document.getElementById("file-input");
    formData.append("file", fileInput.files[0]);
    const fileType = document.querySelector('input[name="file_type"]:checked').value;
    formData.append("file_type", fileType);

    // Используем sendRequest для отправки файла
    sendRequest({
        url: "/report_settings/upload_template",  // Обновленный маршрут
        data: formData  
    })
    .then(() => {fileInput.value = "";})
    .catch(error => {fileInput.value = "";});
});
