from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///customers.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 客户信息模型
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_name = db.Column(db.String(100), nullable=False)
    wechat_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    preferred_time = db.Column(db.String(200))
    competition_experience = db.Column(db.Text)
    needs = db.Column(db.Text)
    recommended_class = db.Column(db.String(100))
    trial_class_time = db.Column(db.Date)
    future_trial_time = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_trial_confirmed = db.Column(db.Boolean, default=False)

class ClassInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    grade_level = db.Column(db.String(50))
    time_slots = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# CLI命令注册（可选）
from flask.cli import with_appcontext
import click

@click.command(name='create_db')
@with_appcontext
def create_db():
    db.create_all()

app.cli.add_command(create_db) 