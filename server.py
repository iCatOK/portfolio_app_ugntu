app = Flask (__name__)
app.config ['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost/postgres"