// static/js/report_settings.js


document.addEventListener("DOMContentLoaded", function(){
    
    // Вызываем логику добавления типов отчетов
    initAddTypeListener(); 
    // Вызываем логику удаления типов отчетов
    initDeleteTypeListener();
    // Вызываем логику редактирования типов отчетов
    initEditTypeListener();
    
    // Вызываем логику добавления подтипов отчетов
    initAddSubtypeListener();
    // Вызываем логику удаления подтипов отчетов
    initDeleteSubtypeListener();
    // Вызываем логику редактирования подтипов отчетов
    initEditSubtypeListener();

    // Вызываем логику добавления типов параграфов
    initAddParagraphTypeListener();
     // Вызываем логику загрузки файлов шаблона Word и росписи
    initFileUploadListener();
});

// Функция для добавления нового типа отчета
function initAddTypeListener() {
    const typeForm = document.getElementById('type-form');
    if (!typeForm) return; // Проверяем, есть ли форма на странице

    typeForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // Предотвращаем отправку формы и перезагрузку страницы

        const input = document.getElementById('new_type');
        const newTypeName = input.value.trim();

        if (!newTypeName) {
            toastr.error('Type name cannot be empty.');
            return;
        }

        try {
            const response = await sendRequest({
                url: '/report_settings/add_type',  // URL для добавления нового типа
                method: 'POST',
                data: { new_type: newTypeName },
                csrfToken: csrfToken
            });

            // Если запрос успешен, обновляем список типов на странице
            if (response.status === 'success') {
                const typesList = document.getElementById('types-list');
                const newListItem = document.createElement('li');
                newListItem.textContent = newTypeName;
                typesList.appendChild(newListItem);

                input.value = ''; // Очищаем поле ввода
                toastr.success(response.message);
            } else {
                alert(response.message);
            }
        } catch (error) {
            alert(error.message || 'An error occurred while adding the type.');
        }
    });
}

// Логика для удаления типа отчета
function initDeleteTypeListener() {
    const deleteButtons = document.querySelectorAll('.report-section__btn--delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', async function(event) {
            event.preventDefault();
            
            const typeId = this.dataset.typeId;

            if (!typeId) {
                toastr.error('Type ID is missing.');
                return;
            }

            const confirmation = confirm('Are you sure you want to delete this type?');
            if (!confirmation) return;
            try {
                const response = await sendRequest({
                    url: '/report_settings/delete_type',  // Маршрут для удаления типа
                    data: { type_id: typeId },
                    csrfToken: csrfToken
                });

                if (response.status === 'success') {
                    // Удаляем элемент типа из DOM
                    this.closest('li').remove();
                } 
            } catch (error) {
                console.log('An error occurred while deleting the type.');
            }
        });
    });
}


// Логика для редактирования типа отчета
function initEditTypeListener() {
    const editButtons = document.querySelectorAll('.report-section__btn--edit');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const typeId = this.dataset.typeId;
            const typeInput = this.closest('li').querySelector('.report-section__input--type');  // Найти поле ввода для редактирования
            const newTypeName = typeInput.value.trim();

            if (!newTypeName) {
                toastr.error('Type name cannot be empty.');
                return;
            }

            sendRequest({
                url: '/report_settings/edit_type',  
                data: { type_id: typeId, new_type_name: newTypeName },
                csrfToken: csrfToken
            })
            .catch(error => {
                console.log('An error occurred while editing the type.');
            });
        });
    });
}


// Логика для добавления нового подтипа отчета
function initAddSubtypeListener() {
    const subtypeForm = document.getElementById('subtype-form');
    if (!subtypeForm) return;  // Проверяем наличие формы на странице

    subtypeForm.addEventListener('submit', async function(event) {
        event.preventDefault();  // Предотвращаем стандартную отправку формы

        const typeSelect = document.getElementById('report_subtype_type');
        const newSubtypeInput = document.getElementById('new_subtype');
        const reportTypeId = typeSelect.value;
        const newSubtypeName = newSubtypeInput.value.trim();

        if (!newSubtypeName) {
            toastr.error('Subtype name cannot be empty.');
            return;
        }

        try {
            const response = await sendRequest({
                url: '/report_settings/add_subtype',  
                data: { report_type_id: reportTypeId, new_subtype_name: newSubtypeName },
                csrfToken: csrfToken
            });

            if (response.status === 'success') {
                // Обновляем список подтипов на странице
                const subtypesList = document.getElementById('subtypes-list');
                const newListItem = document.createElement('li');
                newListItem.textContent = `${newSubtypeName} (Type ID: ${reportTypeId})`;
                subtypesList.appendChild(newListItem);

                newSubtypeInput.value = '';  // Очищаем поле ввода
                
            } 
        } catch (error) {
            console.log('An error occurred while adding the subtype.');
        }
    });
}


// Логика для удаления подтипа отчета
function initDeleteSubtypeListener() {
    const deleteButtons = document.querySelectorAll('.delete-subtype-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', async function(event) {
            event.preventDefault();

            const subtypeId = this.dataset.subtypeId;

            if (!subtypeId) {
                toastr.error('Subtype ID is missing.');
                return;
            }

            const confirmation = confirm('Are you sure you want to delete this subtype?');
            if (!confirmation) return;

            try {
                const response = await sendRequest({
                    url: '/report_settings/delete_subtype',
                    data: { subtype_id: subtypeId },
                    csrfToken: csrfToken
                });

                if (response.status === 'success') {
                    // Удаляем элемент подтипа из DOM
                    this.closest('li').remove();
                } 
            } catch (error) {
                console.log('An error occurred while deleting the subtype.');
            }
        });
    });
}


// Логика для редактирования подтипа отчета
function initEditSubtypeListener() {
    const editButtons = document.querySelectorAll('.edit-subtype-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const subtypeId = this.dataset.subtypeId;
            const subtypeInput = this.closest('li').querySelector('.subtype-input');  // Найти поле ввода для редактирования
            const newSubtypeName = subtypeInput.value.trim();
            if (!newSubtypeName) {
                toastr.error('Subtype name cannot be empty.');
                return;
            }
            try {
                await sendRequest({
                    url: '/report_settings/edit_subtype',
                    data: { subtype_id: subtypeId, new_subtype_name: newSubtypeName },
                    csrfToken: csrfToken
                });
            } catch (error) {
                console.log('An error occurred while editing the subtype.');
            }
        });
    });
}



// Логика для добавления нового типа параграфа
function initAddParagraphTypeListener() {
    const paragraphForm = document.getElementById('paragraph-type-form');
    if (!paragraphForm) return; // Проверяем, есть ли форма на странице

    paragraphForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // Предотвращаем отправку формы и перезагрузку страницы

        const input = document.getElementById('new_paragraph_type');
        const newTypeName = input.value.trim();

        if (!newTypeName) {
            toastr.error('Paragraph type name cannot be empty.');
            return;
        }

        try {
            const response = await sendRequest({
                url: '/report_settings/add_paragraph_type',
                method: 'POST',
                data: { new_paragraph_type: newTypeName },
                csrfToken: csrfToken
            });

            // Если запрос успешен, обновляем список типов параграфов на странице
            if (response.status === 'success') {
                const paragraphTypesList = document.getElementById('paragraph-types-list');
                const newListItem = document.createElement('li');
                newListItem.textContent = newTypeName;
                paragraphTypesList.appendChild(newListItem);

                input.value = ''; // Очищаем поле ввода
                toastr.success(response.message);
            } else {
                alert(response.message);
            }
        } catch (error) {
            alert(error.message || 'An error occurred while adding the paragraph type.');
        }
    });
}


// Логика для загрузки файла шаблона на сервер
function initFileUploadListener() {
    const fileUploadForm = document.getElementById('file-upload-form');
    if (!fileUploadForm) return; // Проверяем, есть ли форма на странице

    fileUploadForm.addEventListener('submit', function(event) {
        event.preventDefault(); // Предотвращаем отправку формы и перезагрузку страницы

        const formData = new FormData();
        const fileInput = document.getElementById('file-input');
        formData.append('file', fileInput.files[0]);
        const fileType = document.querySelector('input[name="file_type"]:checked').value;
        formData.append('file_type', fileType);

        sendRequest({
            url: '/report_settings/upload_template',
            data: formData
        })
        .then(() => {
            fileInput.value = ''; // Очищаем поле ввода
        })
        .catch(error => {
            fileInput.value = ''; // Очищаем поле ввода при ошибке
        });
    });
}

