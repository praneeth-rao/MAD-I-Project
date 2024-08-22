from flask_restful import Resource, Api
from flask import jsonify, Blueprint
from LMS.db import get_db

bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(bp)

class Books(Resource):
    def get(self):
            db = get_db()
            all_books = db.execute(
            'SELECT books.id, books.name, books.author, books.description'
            ' FROM books'
            ).fetchall()

            data=[]
            for book in all_books:
                  data.append({"id" : book['id'],
                               "name" : book['name'],
                               "author" : book['author'],
                               "description":book["description"]
                               })
            return jsonify({"Books": data})

api.add_resource(Books, '/books')