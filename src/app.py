"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User

# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False


class TodoList:
    _id_counter = 1
    todos = [
        {"done": True, "label": "Sample Todo 1", "id": 0},
        {"done": True, "label": "Sample Todo 2", "id": 1},
    ]

    def _get_new_ID(self):
        self._id_counter += 1
        return self._id_counter

    def get_todos(self):
        return self.todos

    def add_todo(self, new_todo):
        todo_to_add = {**new_todo, "id": self._get_new_ID()}
        self.todos = [*self.todos, todo_to_add]

    def delete_todo(self, id):
        updated_todos = list(filter(lambda todo: todo["id"] != id, self.todos))
        self.todos = updated_todos

    def update_todo(self, id, updated_incoming_todo):
        [todo_to_update] = list(filter(lambda todo: todo["id"] == id, self.todos))
        todos_not_updated = list(filter(lambda todo: todo["id"] != id, self.todos))
        updated_todo = {**todo_to_update, **updated_incoming_todo}
        self.todos = [*todos_not_updated, updated_todo]
        return {"updated_from": todo_to_update, "updated_to": updated_todo}


db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace(
        "postgres://", "postgresql://"
    )
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)


# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


# generate sitemap with all your endpoints
@app.route("/")
def sitemap():
    return generate_sitemap(app)


@app.route("/user", methods=["GET"])
def handle_hello():
    response_body = {"msg": "Hello, this is your GET /user response "}

    return jsonify(response_body), 200


todo_list = TodoList()


@app.route("/todo", methods=["GET"])
def get_todos():
    return jsonify(todo_list.get_todos()), 200


@app.route("/todo", methods=["POST"])
def add_todo():
    request_body = request.json
    todo_list.add_todo(request_body)

    updated_list = todo_list.get_todos()
    return (
        jsonify(
            {
                "message": "Successfully created and added task to ToDo List",
                "updated_list": updated_list,
            }
        ),
        200,
    )


@app.route("/todo/<int:id>", methods=["PUT"])
def update_todo(id):
    request_body = request.json
    update_data = todo_list.update_todo(id, request_body)
    return (
        jsonify(
            {
                "message": "Successfully updated task and updated ToDo List",
                "updated_from": update_data["updated_from"],
                "updated_to": update_data["updated_to"],
            }
        ),
        200,
    )


@app.route("/todo/<int:id>", methods=["DELETE"])
def delete_todo(id):
    todo_list.delete_todo(id)
    updated_list = todo_list.get_todos()
    return (
        jsonify(
            {
                "message": "Successfully deleted task and updated ToDo List",
                "updated_list": updated_list,
            }
        ),
        200,
    )


# this only runs if `$ python src/app.py` is executed
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=PORT, debug=False)
