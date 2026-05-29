import traceback
from flask import jsonify
from app.services.logging_service import LoggingService


def init_error_logger(app):

    @app.errorhandler(Exception)
    def handle_exception(error):

        LoggingService.error(
            f"""
            GLOBAL EXCEPTION
            ERROR: {str(error)}

            TRACEBACK:
            {traceback.format_exc()}
            """
        )

        return jsonify({
            "error": "Ha ocurrido un error interno"
        }), 500