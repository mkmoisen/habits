import os
SECRET_KEY = os.environ.get('HABITS_SECRET_KEY', 'abc') # secrets.token_hex())

DATABASE_NAME = os.environ.get('HABITS_DATABASE_NAME', 'habits')
DATABASE_USERNAME = os.environ.get('HABITS_DATABASE_USERNAME', 'habits')
DATABASE_PASSWORD = os.environ.get('HABITS_DATABASE_PASSWORD', 'habits')
DATABASE_HOST = os.environ.get('HABITS_DATABASE_HOST', 'habits-database-1')
DATABASE_PORT = os.environ.get('HABITS_DATABASE_PORT', '5432')