// static/js/report_settings.js


document.addEventListener("DOMContentLoaded", function(){

    // Слушатель на селект для выбора типа отчета
    document.getElementById('reportTypesDefault').addEventListener('change', function() {
        reportTypesSelect(this);
    });

    // Слушатель на селект для выбора подтипа отчета
    document.getElementById('reportSubtypesDefault').addEventListener('change', function() {
        reportSubtypesSelect(this);
    });

    // Слушатель для кнопки "Добавить тип отчета"
    document.getElementById('newTypeButton').addEventListener('click', function() {
       addNewType();
    });
    
    // Слушатели для кнопок Удалить тип отчета
    document.querySelectorAll('.report-settings__btn--delete-type').forEach(button => {
        button.addEventListener("click", function(){
            deleteType(this);
        })
    });

    // Слушатели для кнопок Редактировать тип отчета
    document.querySelectorAll('.report-settings__btn--edit-type').forEach(button => {
        button.addEventListener("click", function(){
            editType(this);
        });
    })

    // Слушатель для кнопки "Добавить подтип отчета"
    document.getElementById('newSubtypeButton').addEventListener('click', function() {
        addSubtype();
    });

    // Слушатели для кнопок Удалить подтип
    document.querySelectorAll(".report-settings__btn--delete-subtype").forEach(button => {
        button.addEventListener("click", function() {
            deleteSubtype(this);
        });
    });

    // Слушатели для кнопок Редактировать подтип
    document.querySelectorAll(".report-settings__btn--edit-subtype").forEach(button => {
        button.addEventListener("click", function() {
            editSubtype(this);
        });
    });
    
    
     // Вызываем логику загрузки файлов шаблона Word и росписи
    initFileUploadListener();

    // Слушатель на селект для выбора типа отчета
    document.getElementById('reportTypes').addEventListener('change', function() {
        showSelectedType(this);
    });

    // Инициализация отображения выбранного типа отчета через эмуляцию события
    const reportTypeSelect = document.getElementById('reportTypes');
    const event = new Event('change');
    reportTypeSelect.dispatchEvent(event);
       
});


// Функция для обработки выбора типа отчета
function reportTypesSelect(select) {
    const selectedType = select.value;
    const newTypeInput = document.getElementById('newTypeLabel');

    if (selectedType === 'new_type') {
        newTypeInput.style.display = 'block'; // Показываем поле для ввода нового типа
    }
    else {
        newTypeInput.style.display = 'none'; // Скрываем поле для ввода нового типа
    }
}

// Функция для обработки выбора подтипа отчета
function reportSubtypesSelect(select) {
    const selectedSubtype = select.value;
    const newSubtypeInput = document.getElementById('newSubtypeLabel');
    
    if (selectedSubtype === 'new_subtype') {
        newSubtypeInput.style.display = 'block'; // Показываем поле для ввода нового подтипа
    }
    else {
        newSubtypeInput.style.display = 'none'; // Скрываем поле для ввода нового подтипа
    }
}


// Функция для добавления нового типа отчета
async function addNewType() {
    const newTypeLabel = document.getElementById('newTypeLabel');
    const newTypeInput = document.getElementById('newTypeInput');
    const newTypeSelect = document.getElementById('reportTypesDefault');

    let newTypeForRequest = newTypeSelect.value;
    if (newTypeForRequest === 'new_type') {
        newTypeForRequest = newTypeInput.value.trim();
    }
       

    if (!newTypeForRequest) {
        toastr.error('Поле с именем нового типа не должно быть пустым.');
        return;
    }

    try {
        const response = await sendRequest({
            url: '/report_settings/add_type',  // URL для добавления нового типа
            data: { new_type: newTypeForRequest },
        });

        // Если запрос успешен, обновляем список типов на странице
        if (response.status === 'success') {
            window.location.reload(); 
        } else if (response.status === 'warning') {
            console.warn('такой тип уже есть в бд для данного профиля', response.message);
        }
    } catch (error) {
        alert(error.message || 'Ошибка при добавлении типа протокола.');
    }
}


// Логика для удаления типа отчета
async function deleteType(button) {
    const typeId = button.getAttribute('data-type-id');
    if (!typeId) {
        toastr.error('Не найден ID типа.');
        return;
    }
    const confirmation = confirm('Вы уверены что хотите удалить этот тип протокола? Будут автоматически удалены ВСЕ подтипы и ВСЕ связанные с ними протоколы.');
    if (!confirmation) return;

    try {
        const response = await sendRequest({
            url: '/report_settings/delete_type',  // Маршрут для удаления типа
            data: { type_id: typeId },
        });

        if (response.status === 'success') {
            window.location.reload();  // Перезагружаем страницу для обновления списка типов
        } 
    } catch (error) {
        console.log(error.message || 'Ошибка при удалении типа протокола.');
    }
}


// Логика для редактирования типа отчета
async function editType(button) {
    const typeId = button.getAttribute('data-type-id');
    const typeInput = button.closest('li').querySelector('.report-settings__input--type');  // Найти поле ввода для редактирования
    const newTypeName = typeInput.value.trim();

    if (!newTypeName) {
        toastr.error('Поле с именем типа не должно быть пустым.');
        return;
    }

    try {
        const response = await sendRequest({
            url: '/report_settings/edit_type',  
            data: { type_id: typeId, new_type_name: newTypeName },
        });

        if (response.status === 'success') {
            // Обновляем текст типа на странице
            window.location.reload();
        } else {
            console.error('Ошибка при редактировании типа протокола:', response.message);
        }
    } catch (error) {
        console.log(error.message || 'Ошибка при редактировании типа протокола.');
    }
    
}


// Логика для добавления нового подтипа отчета
async function addSubtype() {
    const typeSelect = document.getElementById('reportTypes');
    const newSubtypeInput = document.getElementById('newSubtypeInput');
    const reportTypeId = typeSelect.value;
    const subtypeDefault = document.getElementById('reportSubtypesDefault');

    let newSubtypeForRequest = subtypeDefault.value;

    if (newSubtypeForRequest === 'new_subtype') {
        newSubtypeForRequest = newSubtypeInput.value.trim();
    }


    if (!newSubtypeForRequest || !reportTypeId) {
        toastr.error('Поле с именем нового подтипа не должно быть пустым и должен быть выбран тип протокола.');
        return;
    }

    try {
        const response = await sendRequest({
            url: '/report_settings/add_subtype',  
            data: { report_type_id: reportTypeId, new_subtype_name: newSubtypeForRequest },
        });

        if (response.status === 'success') {
            // Обновляем список подтипов на странице
            window.location.reload();
        } 
    } catch (error) {
        console.log(error.message || 'Ошибка при добавлении подтипа протокола.');
    }
}

// Логика для отображения выбранного типа отчета
function showSelectedType(select) {
    const selectedTypeId = select.value;
    const reportTypes = document.querySelectorAll('.report-settings__item--subtype');

    reportTypes.forEach(type => {
        if (type.getAttribute('data-type-id') === selectedTypeId) {
            console.log('show');
            type.style.display = 'flex';
        } else {
            console.log('hide');
            type.style.display = 'none';
        }
    });
}

// Логика для удаления подтипа отчета
async function deleteSubtype(button) {
    const subtypeId = button.getAttribute('data-subtype-id');

    if (!subtypeId) {
        toastr.error('Не найден ID подтипа.');
        return;     
    }

    const confirmation = confirm('Вы уверены что хотите удалить этот подтип? Будут автоматически удалены ВСЕ связанные с ним протоколы.');
    if (!confirmation) return;

    try {
        const response = await sendRequest({
            url: '/report_settings/delete_subtype',
            data: { subtype_id: subtypeId },
        });

        if (response.status === 'success') {
            window.location.reload();
        } 
    } catch (error) {
        console.log(error.message || 'Ошибка при удалении подтипа протокола.');
    }
}


// Логика для редактирования подтипа отчета
async function editSubtype(button) {
    const subtypeId = button.getAttribute('data-subtype-id');
    const subtypeInput = button.closest('li').querySelector('.report-settings__input--subtype'); 
    const newSubtypeName = subtypeInput.value.trim();
    if (!newSubtypeName) {
        toastr.error('Имя подтипа не должно быть пустым.');
        return;
    }
    try {
        await sendRequest({
            url: '/report_settings/edit_subtype',
            data: { subtype_id: subtypeId, new_subtype_name: newSubtypeName },
        });
    } catch (error) {
        console.log(error.message || 'Ошибка при редактировании подтипа протокола.');
    }
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
            data: formData,
            csrfToken: csrfToken
        })
        .then(() => {
            fileInput.value = ''; // Очищаем поле ввода
        })
        .catch(error => {
            fileInput.value = ''; // Очищаем поле ввода при ошибке
        });
    });
}

