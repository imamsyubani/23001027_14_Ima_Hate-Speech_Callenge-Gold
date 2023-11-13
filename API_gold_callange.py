import chardet
import json
import re
import os
from flask import Flask, jsonify
from flask import request
import flask
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
import pandas as pd
import sqlite3

app = Flask(__name__)

app.json_encoder = LazyJSONEncoder
swagger_template = dict(
    info={
        'title': "API Documentation for Data Processing and Modeling",
        'version': "1.0.0",
        'description': "Dokumentasi API untuk Data Processing dan Modeling",
    },
    host="127.0.0.1:5000/"
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "docs",
            "route": "/docs.json",
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template, config=swagger_config)


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to SQLite version {sqlite3.version}")
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table_if_not_exists_data_text(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_text (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processed_text TEXT
        )
    ''')


def create_table_if_not_exists_data_csv(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_csv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column1 TEXT,
            column2 TEXT
                   
        )
    ''')


def cleansing_text(text):
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'\burl\b', '', text)
        text = re.sub(r'\\[^\s]+', '', text)
        text = re.sub(r'rt|wk|[^\w\s]', '', text)
        text = re.sub(r'[^a-zA-Z0-9]', ' ', text)
        text = re.sub(r'rt|user|[^\w\s]', '', text)
        text = re.sub(r'rt|url|[^\w\s]', '', text)
        text = re.sub(r'\d', '', text)
        text = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))', ' ', text)
        text = re.sub('  +', ' ', text)
    return text


@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'description': "Menyapa Hello Semua",
        'data': "Hello World",
    }
    response_data = jsonify(json_response)
    return response_data


@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/text', methods=['GET'])
def text():
    json_response = {
        'status_code': 200,
        'description': "saya IMAM SYUBANI",
        'data': "Halo, apa kabar semua?",
    }
    response_data = jsonify(json_response)
    return response_data


@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/text-clean', methods=['GET'])
def text_clean():
    json_response = {
        'status_code': 200,
        'description': "Original Teks",
        'data': re.sub(r'[^a-zA-Z0-9]', ' ', "Halo, saya imam syubani!"),
    }
    response_data = jsonify(json_response)
    return response_data


@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():
    text = request.form.get('text')
    text_processing = cleansing_text(text)

    # Connect to SQLite database
    conn = create_connection('data_text.db')
    with conn:
        cursor = conn.cursor()
        create_table_if_not_exists_data_text(cursor)
        cursor.execute('INSERT INTO data_text (processed_text) VALUES (?)', (text_processing,))
        conn.commit()

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses dan disimpan ke dalam database",
        'processed_text': text_processing,
    }

    response_data = jsonify(json_response)
    return response_data


@swag_from("docs/upload_csv.yml", methods=['POST'])
@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    with open(file.filename, 'rb') as f:
        result = chardet.detect(f.read())

    encoding = result['encoding']

    # Read CSV data into a DataFrame
    data = pd.read_csv(file, encoding=encoding)

    # Connect to SQLite database
    conn = create_connection('data_file.db')
    with conn:
        cursor = conn.cursor()
        create_table_if_not_exists_data_text(cursor)
        create_table_if_not_exists_data_csv(cursor)

        for col in data.columns:
            data[col] = data[col].apply(cleansing_text)

        data.to_sql('data_csv', conn, if_exists='replace', index=False)


    json_response = {
        'status_code': 200,
        'description': "File CSV yang sudah diproses dan disimpan ke dalam database",
        'processed_data': data.to_json(),
    }

    response_data = jsonify(json_response)
    return response_data


   
if __name__ == '__main__':
    app.run()
