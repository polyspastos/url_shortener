__version__ = "0.1.1"

import logging
import os
import random
import re
import string
import sys
from os import getenv
from pathlib import Path
from typing import Text
from urllib import response
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, json, jsonify, request
from flask_restful import Api, Resource
from sqlalchemy import Column, create_engine, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import exists
from sqlalchemy_utils import create_database, database_exists

from models import Shortcode, db

APP_DIR = Path(__file__).parent
log = logging.getLogger()


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
print(PROJECT_DIR)
sys.path.append(PROJECT_DIR)


load_dotenv()
app = Flask(__name__)
api = Api(app)

postgrespath = getenv("POSTGRESPATH")
database_name = getenv("DATABASE_NAME")
database_path = postgrespath + "/" + database_name

app.config["SQLALCHEMY_DATABASE_URI"] = database_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
# app.config['SECRET_KEY'] = 'hmmm'

db.init_app(app)


def is_valid_shortcode(shortcode):
    assert isinstance(shortcode, Text)

    is_alnum_plus_underscore = re.search(r"^[a-zA-Z0-9_]*$", shortcode)
    log.info(f"is_alnum_plus_underscore: {is_alnum_plus_underscore}")
    if len(shortcode) != 6 or (is_alnum_plus_underscore is None):
        return False
    else:
        return True


def is_valid_url(url):
    assert isinstance(url, Text)

    valid_url = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if re.match(valid_url, url) is not None:
        return True
    else:
        return False


class InitializeDatabase(Resource):
    conn_string = database_path
    engine = create_engine(conn_string)

    def get(self):
        if not database_exists(database_path):
            create_database(database_path)
            result = "Database created."
        else:
            result = "Database already created."
        db.metadata.create_all(self.engine)
        if "already" in result:
            result += " Database tables already created."
        else:
            result += " Database tables created."
        log.info(result)
        return jsonify(result)


class Shortener(Resource):
    def post(self):
        conn_string = database_path
        engine = create_engine(conn_string)

        request_data = request.get_json()
        logging.info(f"request_data: {request_data}")

        error_message = ""
        proceed = True

        try:
            url = request_data["url"]
        except KeyError:
            url = ""
            status = 400
            error_message = "Url not present"

        if not is_valid_url(url):
            status = 400
            error_message = "Invalid url"
            shortcode = "n/a"
            proceed = False

        if url and proceed:
            try:
                shortcode = request_data["shortcode"]
            except KeyError:
                shortcode = "".join(
                    random.choices(string.ascii_letters + string.digits + "_", k=6)
                )

            logging.info(f"shortcode: {shortcode}")

            Session = sessionmaker(bind=engine)
            session = Session()

            shortcode_exists = db.session.query(
                session.query(Shortcode).filter_by(shortcode=shortcode).exists()
            ).scalar()

            log.info(f"shortcode_exists: {shortcode_exists}")

            if not shortcode_exists:
                if is_valid_shortcode(shortcode):
                    try:
                        new_shortcode = Shortcode(
                            url, shortcode, func.now(), func.now(), 0
                        )

                        session.add(new_shortcode)
                        session.commit()

                        logging.info(f"new shortcode in db: {shortcode}")

                        status = 201

                    except IntegrityError as e:
                        log.error(e)
                        session.rollback()
                    finally:
                        session.close()
                else:
                    status = 412
                    error_message = "The provided shortcode is invalid"
            else:
                status = 409
                error_message = "Shortcode already in use"

        response = app.response_class(
            response=json.dumps(
                {"shortcode": shortcode, "error_message": error_message}
            ),
            status=status,
            mimetype="application/json",
        )

        return response


class ShortcodeChecker(Resource):
    def get(self, shortcode):
        status = 404
        location = ""
        if is_valid_shortcode(shortcode):
            logging.info(f"valid shortcode checked: {shortcode}")
            status = 302
            # error_message = ""

            conn_string = database_path
            engine = create_engine(conn_string)

            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                shortcode_entry_to_alter = (
                    session.query(Shortcode)
                    .filter_by(shortcode=shortcode)
                    .one_or_none()
                )
                if shortcode_entry_to_alter is not None:
                    shortcode_entry_to_alter.redirect_last = func.now()
                    shortcode_entry_to_alter.redirect_count += 1

                location = shortcode_entry_to_alter.url

                session.commit()
            except IntegrityError as e:
                log.error(e)
                session.rollback()
            finally:
                session.close()

        response = app.response_class(
            response="",
            status=status,
        )

        response.headers["Location"] = location

        return response


class StatCreator(Resource):
    def get(self, shortcode):
        if is_valid_shortcode(shortcode):
            logging.info(f"valid shortcode checked for stats: {shortcode}")

            conn_string = database_path
            engine = create_engine(conn_string)

            Session = sessionmaker(bind=engine)
            session = Session()

            shortcode_entry_to_poll = (
                session.query(Shortcode).filter_by(shortcode=shortcode).one_or_none()
            )
            if shortcode_entry_to_poll is not None:
                created = shortcode_entry_to_poll.created
                redirect_last = shortcode_entry_to_poll.redirect_last
                redirect_count = shortcode_entry_to_poll.redirect_count

            session.close()

            response = app.response_class(
                response=json.dumps(
                    {
                        "created": created,
                        "lastRedirect": redirect_last.isoformat(),
                        "redirectCount": redirect_count,
                    }
                ),
                status=200,
                mimetype="application/json",
            )
        else:
            response = app.response_class(
                response=json.dumps(
                    {"shortcode": shortcode, "error_message": "Shortcode not found"}
                ),
                status=404,
                mimetype="application/json",
            )

        return response


@app.before_first_request
def initialize_api():
    add_resources()
    log.info("API resources imported. Ready to receive HTTP requests.")


def add_resources():
    api.add_resource(InitializeDatabase, "/init")
    api.add_resource(Shortener, "/shorten", methods=["POST"])
    api.add_resource(ShortcodeChecker, "/", "/<string:shortcode>")
    api.add_resource(StatCreator, "/", "/<string:shortcode>/stats")


if __name__ == "__main__":
    handler = logging.FileHandler(APP_DIR / "url_shortener.log")
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    app.run(debug=True)
