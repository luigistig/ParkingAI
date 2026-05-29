from flask import request
from time import time
from app.services.logging_service import LoggingService


def init_request_logger(app):

    @app.before_request
    def before_request():
        request.start_time = time()

        LoggingService.info(
            f"""
            REQUEST STARTED
            METHOD: {request.method}
            URL: {request.url}
            IP: {request.remote_addr}
            USER_AGENT: {request.user_agent}
            """
        )

    @app.after_request
    def after_request(response):

        duration = time() - request.start_time

        LoggingService.info(
            f"""
            REQUEST FINISHED
            STATUS: {response.status}
            DURATION: {duration:.4f}s
            """
        )

        return response