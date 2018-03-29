#!/usr/bin/env python
from flask import Flask
from models.shared import db
from models.shared import login_manager
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from models.users import *
from models.log import *
from models.brands import *
from models.tools import *
from models.lists import *
from models.list_subscribers import *
from models.folders import *
from models.forms import *
from models.imports import *
from models.system_jobs import *
from models.exports import *
from models.api_log import *
from models.templates import *
from models.system_merge_fields import *
from models.emails import *
from models.segments import *
from models.campaigns import *
from models.data_views import *
from models.file_locations import *
import os
from routes.main import main
from routes.users import users
from routes.brands import brands
from routes.tools import tools
from routes.subscribers import subscribers
from routes.content import content
from routes.activities import activities
from routes.tracking import tracking
from routes.admin import admin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres2:!postgres#15@localhost/gmancoder_mmc'
app.secret_key = os.urandom(24)
app.jinja_env.autoescape = False
db.init_app(app)
login_manager.login_view = "main.login"
login_manager.init_app(app)
app.register_blueprint(main)
app.register_blueprint(users)
app.register_blueprint(brands)
app.register_blueprint(tools)
app.register_blueprint(subscribers)
app.register_blueprint(content)
app.register_blueprint(activities)
app.register_blueprint(tracking)
app.register_blueprint(admin)


migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
