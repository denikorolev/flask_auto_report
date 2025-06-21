# app/handlers/error.py

from flask import render_template

def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Errorhandler: {str(e)}")
        return f"Internal Server Error {str(e)}", 500