import string, random, json, sys, os.path, uuid
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
# from models import sesion
import models.models as database
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.functions import func
import uuid
from config.config import env
from werkzeug.utils import secure_filename
from flask import flash, redirect, url_for, jsonify

## Chequear que solo existe una extension
def allowed_file(filename, type):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in (env['ALLOWED_EXTENSIONS_BOOKS'] if type == 'book' else env['ALLOWED_EXTENSIONS_IMG'])

def id_generator(size=150, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count

class LibrosCtrl(object):
    @staticmethod
    def all(page_num, db, response):
        try:
            res = {
                'success': False,
            }
            total = database.Libro.query.filter(database.Libro.activo == 1)
            books = database.Libro.query.filter(database.Libro.activo == 1).paginate(page=int(page_num), per_page=24).items
            if books == None:
                res['books'] = []
            else:
                # print(books.comentarios)
                serialized = [ { 'id': i.id,
                                'name': i.nombre_libro,
                                'file': i.nombre_archivo,
                                'author': i.autor,
                                'likes': i.likes,
                                'licencia': i.licencia,
                                'image': i.imagen } for i in books ]
                res['books'] = serialized
            res['success'] = True
            res['total'] = get_count(total)
        except Exception as e:
            print(e)
            # db.session.rollback()
            res['msg'] = 'Hubo un error al obtener los libros, inténtelo nuevamente'
        finally:
            return response(json.dumps(res), mimetype='application/json')

    @staticmethod
    def getBook(book_id, db, response):
        try:
            res = {
                'success': False,
            }
            book = database.Libro.query.get(book_id)
            res['success'] = True
            res['book'] = book
        except Exception as e:
            print(e)
            # db.session.rollback()
            res['msg'] = 'Hubo un error al cargar el libro, inténtelo nuevamente'
        finally:
            return response(json.dumps(res), mimetype='application/json')

    @staticmethod
    def searchBook(query_p, db, response):
        try:
            res = {
                'success': False,
            }
            books = database.Libro.query.filter(
                    database.Libro.autor.like('%{}%'.format(query_p)) |
                    database.Libro.nombre_libro.like('%{}%'.format(query_p))
                    ).all()
            if books == None:
                res['books'] = []
            else:
                # print(books.comentarios)
                serialized = [ { 'id': i.id,
                                'name': i.nombre_libro,
                                'file': i.nombre_archivo,
                                'author': i.autor,
                                'likes': i.likes,
                                'licencia': i.licencia,
                                'image': i.imagen } for i in books ]
                res['books'] = serialized

            res['success'] = True
        except Exception as e:
            print(e)
            # db.session.rollback()
            res['msg'] = 'Hubo un error al cargar el libro, inténtelo nuevamente'
        finally:
            return response(json.dumps(res), mimetype='application/json')

    @staticmethod
    def uploadBook(db, request, response):
        print(request.form)
        print(request.files)
        try:
            res = {
                'success': False,
            }
            if request.method == 'POST':
                print('reached1')
                if 'filebook' not in request.files and 'fileimg' not in request.files:
                    flash('No existe el archivo')
                    return redirect(request.url)
                bookfile = request.files['filebook']
                imgfile = request.files['fileimg']
                if bookfile.filename == '' and imgfile == '':
                    flash('No se selecciono un archivo')
                    return redirect(request.url)
                print('reached2')
                print(bookfile.filename)
                print(imgfile.filename)
                if (bookfile and allowed_file(bookfile.filename, 'book')) and (imgfile and allowed_file(imgfile.filename, 'img')):
                    bookfilename = uuid.uuid4().hex + secure_filename(bookfile.filename)
                    imgfilename = uuid.uuid4().hex + secure_filename(imgfile.filename)
                    newBook = database.Libro(
                        nombre_libro=request.form['book'],
                        genero=request.form['genre'],
                        autor=request.form['author'],
                        idioma=request.form['language'],
                        licencia=request.form['licence'],
                        nombre_archivo=bookfilename,
                        imagen=imgfilename,
                    )
                    print('reached3')
                    bookfile.save(os.path.join(env['UPLOADS_DIR'] + '/books', bookfilename))
                    imgfile.save(os.path.join(env['UPLOADS_DIR'] + '/images', imgfilename))
                    db.session.add(newBook)
                    db.session.commit()
                    res['success'] = True
                    res['route'] = 'libro-exito'
                    return response(json.dumps(res), mimetype='application/json')
                else:
                    print('err')
                    res['success'] = False
                    res['msg'] = 'Formato no aceptado'
                    res['code'] = 400
            else:
                res['success'] = True
                res['route'] = 'libro-exito'
                return response(json.dumps(res), mimetype='application/json')
        except Exception as e:
            print(e)
            db.session.rollback()
            res['route'] = 'libro-error'
        finally:
            return response(json.dumps(res), mimetype='application/json')
