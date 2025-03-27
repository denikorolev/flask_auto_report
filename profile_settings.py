# profile_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, g, jsonify
from flask_login import current_user
from models import User, UserProfile, db, AppConfig, Paragraph, ReportType, ReportShare
from utils import check_unique_indices
from profile_constructor import ProfileSettingsManager
from flask_security.decorators import auth_required
from file_processing import sync_profile_files
from models import Report
from logger import logger

profile_settings_bp = Blueprint('profile_settings', __name__)

# Functions
def set_profile_settings(profile_id, settings):
    """
    Сохраняет настройки профиля пользователя.
    """
    for key, value in settings.items():
        if not AppConfig.set_setting(profile_id, key, value):
            return False  # Если ошибка — сразу выход
    return True


def set_profile_as_default(profile_id):
    """
    Устанавливает профиль по умолчанию для пользователя.
    """
    logger.info(f"set_profile_as_default started and profile_id = {profile_id}")
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    if not user_profiles:
        return False
    try:
        for profile in user_profiles:
            if profile.id == int(profile_id):
                profile.default_profile = True
                logger.info(f"set profile {profile.id} as default")
            else:
                logger.info(f"set profile {profile.id} as NOT default")
                profile.default_profile = False
            profile.save()
    except Exception as e:
        logger.error(f"set_profile_as_default error {e}")
        return False
    logger.info(f"set_profile_as_default end work successfull")
    return True
    

# Маршрут для загрузки страницы настроек профиля 
@profile_settings_bp.route("/profile_settings", methods=["GET"])
@auth_required()
def profile_settings():
    profile = g.current_profile
    
    if profile:
        return render_template('profile_settings.html', 
                               title="Настройки профиля", 
                               profile=profile)
    else:
        print('Profile not found.', 'danger')
        return redirect(url_for('index'))


# Маршрут для выбора существующего профиля
@profile_settings_bp.route("/choosing_profile", methods=["GET"])
@auth_required()
def choosing_profile():
    # Вот пользователь авторизован и у него либо нет профиля 
    # либо их несколько и нет дефолтного
    logger.info(f"(route 'choosing_profile') --------------------------------------")
    logger.info(f"(route 'choosing_profile') 🚀 Profile settings started and profile in g = {getattr(g,'current_profile', None)}")
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    logger.info(f"(rout 'choosing_profile') User profiles: {user_profiles}")
    if not user_profiles:
        logger.info(f"(route 'choosing_profile') ⚠️ User has no profiles")
        return render_template("choosing_profile.html",
                           title="Создание нового профиля",
                           new_user=True)
    profile_id = request.args.get("profile_id") or None
    logger.info(f"(route 'choosing_profile') Profile id from url: {profile_id}")
    if profile_id:
        logger.info(f"(route 'choosing_profile') Starting profile id from url logic")
        profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
        if profile:
            session["profile_id"] = profile.id
            g.current_profile = profile
            ProfileSettingsManager.load_profile_settings()
            # Синхронизацию файлов пока оставлю здесь, но ее нужно будет перенести
            sync_profile_files(profile.id)
            logger.info(f"(route 'choosing_profile') Profile {profile.id} selected")
            logger.info(f"(route 'choosing_profile') ✅ Profile settings loaded")
            return redirect(url_for("working_with_reports.choosing_report"))
        else:
            logger.error(f"(route 'choosing_profile') ❌ Profile {profile_id} not found or you do not have permission to access it")
            return render_template(url_for("error"),
                           title="Данные о выбранном профиле не получены"
                           )
    logger.info(f"(route 'choosing_profile') Profile id from url not found")
    return render_template("choosing_profile.html",
                           title="Выбор профиля",
                           user_profiles=user_profiles)


# Маршрут для создания профиля
@profile_settings_bp.route("/create_profile", methods=["POST"])
@auth_required()
def create_profile():
    logger.info(f"(route 'create_profile') 🚀 Profile creation started")
    data = request.get_json()
    if not data:
        logger.error(f"(route 'create_profile') ❌ No data received")
        return jsonify({"status": "error", "message": "No data received."}), 400
    
    profile_name = data.get('profile_name')
    description = data.get('description')
    is_default = data.get('is_default')
    
        
    if profile_name:
        logger.info(f"(route 'create_profile') Profile name: {profile_name}")
        try:
            new_profile = UserProfile.create(
                current_user.id, 
                profile_name, 
                description,
                default_profile=is_default
                )
            logger.info(f"(route 'create_profile') Profile {new_profile.id} created")
            default_settings = dict(current_app.config.get("DEFAULT_PROFILE_SETTINGS", {}))
            save_settings = set_profile_settings(new_profile.id, default_settings)

            report_types = []
            current_user_profiles = UserProfile.get_user_profiles(current_user.id)
            for profile in current_user_profiles:
                if profile.id == new_profile.id:
                    continue
                r_types = ReportType.find_by_profile(profile.id)
                for r_type in r_types:
                    report_types.append(r_type)
            for r_type in report_types:
                try:
                    ReportType.create(r_type.type_text, new_profile.id, r_type.type_index)
                    logger.debug(f"(route 'create_profile') Report type {r_type.type_text} created for profile {new_profile.id}")
                except Exception as e:
                    logger.error(f"(route 'create_profile') ❌ Error creating report type {r_type.type_text} for profile {new_profile.id}: {e}")
                    return jsonify({"status": "error", "message": str(e)}), 400
    
        except Exception as e:
            print("creating profile end work {e} --------")
            return jsonify({"status": "error", "message": str(e)}), 400
        
    
    
        if not save_settings:
            return jsonify({"status": "error", "message": "Не получилось сохранить настройки по умолчанию для нового профиля"}), 400
        print("creating profile end work SUCCESS --------")
        return jsonify({"status": "success", "message": "Profile created successfully!"}), 200
    
    print("creating profile end work ERROR no profile name --------")
    return jsonify({"status": "error", "message": "Profile name is required."}), 400


# Маршрут для обновления имени и дескриптора профиля и выбора профиля по умолчанию
@profile_settings_bp.route('/update_profile_settings', methods=['POST'])
@auth_required()
def update_profile_settings():
    data = request.get_json()
    profile_id = data.get("profile_id")
    new_name = data.get("profile_name")
    new_description = data.get("description")
    is_default = data.get("is_default")
    print(f"this profile default = {is_default}")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    
    if profile:
        profile.profile_name = new_name
        profile.description = new_description
        profile.save()
        if is_default:
            set_default = set_profile_as_default(profile_id)
            print(f"Профиль установлен как дефолтный = {set_default}")
            if not set_default:
                notification_message = ["не получилось установить профиль по умолчанию"]
                return jsonify({"status": "succuss","notifications": notification_message, "message": "Изменения сохранены, но"}), 400
        return jsonify({"status": "success", "message": "Данные профиля успешно обновлены!"}), 200
    else:
        return jsonify({"status": "error", "message": "Profile not found or you do not have permission to update it."}), 400



# Маршрут для удаления профиля
@profile_settings_bp.route('/delete_profile/<int:profile_id>', methods=["DELETE"])
@auth_required()
def delete_profile(profile_id):
    print("deleting profile started--------")
    print(f"you are deleting profile and profile_id = {profile_id}")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        try:
            profile.delete()
            print(f"profile {profile_id} deleted")
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        
        session.pop("profile_id", None)
        g.current_profile = None
        return jsonify({"status": "success", "message": "Profile deleted successfully!"}), 200
    else:
        return jsonify({"status": "error", "message": "Profile not found or you do not have permission to delete it."}), 400


# Маршрут для сохранения настроек профиля
@profile_settings_bp.route("/update_settings", methods=["POST"])
@auth_required()
def save_settings():
    """
    Сохраняет настройки профиля пользователя в таблице AppConfig.
    """
    settings = request.json  # Получаем данные из запроса
    profile_id = session.get("profile_id")

    if not profile_id:
        return jsonify({"status": "error", "message": "Profile not selected"}), 400

    save_settings = set_profile_settings(profile_id, settings)
    if not save_settings:
        return jsonify({"status": "error", "message": "Не получилось сохранить настройки"}), 400

    ProfileSettingsManager.load_profile_settings()
    return jsonify({"status": "success", "message": "Settings saved successfully!"})


# Маршрут для установки профиля по умолчанию
@profile_settings_bp.route("/set_default_profile/<int:profile_id>", methods=["POST"])
@auth_required()
def set_default_profile(profile_id):
    if not profile_id:
        return jsonify({"status": "error", "message": "Профиль не выбран"}), 400
    set_default = set_profile_as_default(profile_id)
    if not set_default:
        return jsonify({"status": "error", "message": "Не получилось установить профиль по умолчанию"}), 400
    return jsonify({"status": "success", "message": "Профиль установлен как дефолтный"}), 200



# Маршрут чтобы поделиться с конкретным пользователем всеми протоколами данного профиля
@profile_settings_bp.route("/share_profile", methods=["POST"])
@auth_required()
def share_profile():
    """
    Поделиться профилем с другим пользователем.
    """
    logger.info(f"(route 'share_profile') --------------------------------------")
    logger.info(f"(route 'share_profile') 🚀 Sharing all reports of this profile started")
    data = request.get_json()
    
    email = data.get("email")
    logger.info(f"(route 'share_profile') Recipient email: {email}")
    
    recipient = User.find_by_email(email)
    if not recipient:
        logger.error(f"(route 'share_profile') ❌ User with this email not found")
        return jsonify({"status": "error", "message": "Пользователь с данным email не найден"}), 400
    logger.info(f"(route 'share_profile') Recipient found: {recipient.email}")
    
    try:
        user_id = current_user.id
        profile_id = g.current_profile.id
        profile = UserProfile.find_by_id_and_user(profile_id, user_id)
        all_reports = Report.find_by_profile(profile_id)
    except Exception as e:
        logger.error(f"(route 'share_profile') ❌ Error getting current user or current profile: {e}")
        return jsonify({"status": "error", "message": "Не получилось загрузить данные текощего пользователя или текущего профиля"}), 400
    
    logger.info(f"(route 'share_profile') ✅ Got all necessary data. Starting sharing...")
    
    try:
        for report in all_reports:
            try:
                ReportShare.create(report.id, recipient.id)
            except Exception as e:
                logger.error(f"(route 'share_profile') ❌ Error sharing report {report.report_name}: {e}. Skipping...")
                continue
        logger.info(f"(route 'share_profile') ✅ All reports shared successfully")
        return jsonify({"status": "success", "message": "Профиль успешно поделен"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400




# Маршрут для запуска разных чекеров
@profile_settings_bp.route("/run_checker", methods=["POST"])
@auth_required()
def run_checker():
    """
    Запускает различные чекеры для проверки настроек профиля.
    """
    
    profile_id = session.get("profile_id")
    if not profile_id:
        return jsonify({"status": "error", "message": "Profile not selected"}), 400

    checker = request.json.get("checker")
    
    reports = Report.find_by_profile(profile_id)
    if checker == "main_sentences":
        global_errors = []
        for report in reports:
            paragraphs = Report.get_report_paragraphs(report.id)
            try:
                check_unique_indices(paragraphs)
            except ValueError as e:
                error = {"report": report.report_name, "error": str(e)}
                global_errors.append(error)
    
            try:
                check_unique_indices(paragraphs)
            except ValueError as e:
                error = {"report": report.report_name, "error": str(e)}
                global_errors.append(error)
        
        return jsonify({"status": "success", "message": "Проверка выявила следующие ошибки", "errors": global_errors}), 200
       
    else:
        return jsonify({"status": "error", "message": "Неизвестный чекер"}), 400


# Маршрут для запуска разных чекеров
@profile_settings_bp.route("/fix_indices", methods=["POST"])
@auth_required()
def fix_indices():
    """
    Запускает функцию исправления индексов.
    """
    reports = Report.find_by_profile(g.current_profile.id)  # Получаем все отчеты пользователя
        
    try:
        for report in reports:
            print(f"Исправление индексов для отчета {report.report_name}")
            paragraphs = Paragraph.query.filter_by(report_id=report.id).order_by(Paragraph.paragraph_index).all()
            
            # Обновляем индексы параграфов
            for new_index, paragraph in enumerate(paragraphs):
                paragraph.paragraph_index = new_index

                # Обновляем индексы главных предложений в этом параграфе
                if paragraph.head_sentence_group:
                    head_sentences = sorted(paragraph.head_sentence_group.head_sentences, key=lambda s: s.sentence_index)
                    for new_sentence_index, sentence in enumerate(head_sentences):
                        sentence.sentence_index = new_sentence_index
            
            db.session.commit()  # Сохраняем изменения для всех параграфов и предложений
        logger.info(f"Индексы успешно исправлены")
        return jsonify({"status": "success", "message": "Индексы успешно исправлены"}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при исправлении индексов {e}")
        return jsonify({"status": "error", "message": "Ошибка при исправлении индексов"}), 400
   

