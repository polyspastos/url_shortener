from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.sql import func

from dotenv import load_dotenv

from os import getenv

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask import Flask


app = Flask(__name__)


load_dotenv()

postgrespath = getenv("POSTGRESPATH")
database_name = getenv("DATABASE_NAME")
database_path = postgrespath + "/" + database_name
app.config["SQLALCHEMY_DATABASE_URI"] = database_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True

db = SQLAlchemy(app)
ma = Marshmallow(app)


Base = declarative_base()


class Shortcode(db.Model):
    def __init__(self, url, shortcode, created, redirect_last, redirect_count):
        self.url = url
        self.shortcode = shortcode
        self.created = created
        self.redirect_last = redirect_last
        self.redirect_count = redirect_count

    __tablename__ = "shortcode"
    _id = Column(Integer, primary_key=True)

    url = Column(String, nullable=False)
    shortcode = Column(String, nullable=False, unique=True)
    created = Column(DateTime(timezone=True), server_default=func.now())
    redirect_last = Column(DateTime(timezone=True), onupdate=func.now())
    redirect_count = Column(Integer)


class ShortcodeSchema(ma.Schema):
    class Meta:
        fields = (
            "id_",
            "url",
            "shortcode",
            "created",
            "redirect_last",
            "redirect_count",
        )


shortcode_schema = ShortcodeSchema()
shortcodes_schema = ShortcodeSchema(many=True)
