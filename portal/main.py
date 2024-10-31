from flask import Flask, redirect, url_for, session, render_template_string
from flask_dance.contrib.google import make_google_blueprint, google
from functools import wraps

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from crawler.model.task import Task

app = Flask(__name__)

engine = create_engine("mysql+pymysql://scrapy:12345@localhost/crawler?charset=utf8mb4")
Session = sessionmaker(bind=engine)

@app.route("/")
def home():
    session = Session()
    tasks = session.query(Task).all()

    return render_template_string("""
        <h1>Task Management</h1>
        <table>
        <tr><td>Id</td><td>Type</td><td>Status</td>
        {% for task in tasks %}
            <tr>
            <td>{{ task.id }}</td><td>{{ task.type }}</td><td>{{ task.status}}</td>
            <tr>
        {% endfor %}
        </table>
    """, tasks=tasks)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5080)
