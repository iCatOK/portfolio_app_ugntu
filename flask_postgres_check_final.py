from flask import Flask, jsonify, render_template, url_for, request, flash, redirect, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from utils.custom_orm import get_all_albums_public
from werkzeug.security import generate_password_hash, check_password_hash
from UserLogin import UserLogin

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:koij890hgf@localhost:5433/postgres"
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'kfksofkokfosalfsjk234fdksfl'
app.debug = True
db = SQLAlchemy(app)

Base = automap_base()
Base.prepare(db.engine, reflect=True)

Users = Base.classes.users
Albums = Base.classes.albums
Photos = Base.classes.photos
Reviews = Base.classes.reviews
Likes = Base.classes.likes

# главное меню при анонимном входе
menu = {
    'Главная': 'index',
    'Ввести код': 'index',
    'Вход': 'authorize' 
}

menu_in = menu

# главное меню после входа
menu_out = {
    'Главная': 'index',
    'Ввести код': 'index',
    'Альбомы': 'my_albums',
    'Выйти': 'quit'
}

# меню авторизированного пользователя - редактирование альбома
album_toolbar = {
    'Добавить фото': '',
    'Редактировать описание': '',
    'Приватность':'',
    'Удалить альбом': ''
}

# меню авторизированного пользователя - редактирование фото
photo_toolbar = {
    'Добавить'
}

current_user = None
is_authorized = False

# выход из аккаунта
@app.route('/quit', methods=['GET'])
def quit():
    global current_user
    global is_authorized
    global menu
    current_user = None
    is_authorized = False
    menu = menu_in
    flash('Выход совершен')
    return redirect(url_for('index'))

# альбомы пользователя
@app.route('/myalbums', methods=['GET'])
def my_albums():
    if(current_user is not None):
        print(current_user)
        return redirect(url_for('get_user_albums', nickname=current_user.nickname))
    else:
        flash('что-то не то', 'error')
        return redirect(url_for('index'))

# авторизация
@app.route('/authorize', methods=['GET', 'POST'])
def authorize():
    if request.method == 'POST':
        user = db.session.query(Users).filter_by(nickname=request.form['nick']).first()
        if user is not None and request.form['pass'] == user.user_password:
            global current_user
            global is_authorized
            global menu
            current_user = user
            print(user)
            is_authorized = True
            menu = menu_out
            flash('успешно', 'success')
            return redirect(url_for('index'))
        
        flash('Неверная пара логин/пароль', 'error')

    return render_template('authorization.html', menu=menu)

# регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if len(request.form['nick']) > 4 and len(request.form['password']) > 7:
            user_args = {
                'nickname': request.form['nick'],
                'full_name':request.form['name'],
                'phone_number':request.form['phone'],
                'user_password':request.form['password'],
                'description':request.form['descr']
            }

            if(len(request.form['photo']) != 0):
               user_args['photo_url'] = request.form['photo']

            user = Users(**user_args)
            print(user.full_name)

            

            try:
                db.session.add(user)
                print('добавил')
                db.session.commit()
                print('закомитил')
                flash('Поздравляем, вы зареганы!', 'success')
                return redirect(url_for('authorize'))
            except:
                flash('Не удалось зарегаться (username уже есть в базе или пароль > 30 символов или телефон не российский)', 'error')
        else:
            flash('Неправильно введены данные: username должен быть больше 4 символов, пароль должен быть больше 8 символов', 'error')
    

    return render_template('register.html', menu=menu)

@app.route('/test', methods=['GET'])
def test():
    return {
        'test':'test1'
    }

# главная страница
@app.route('/')
def index():
    allUsers = db.session.query(Users).all()
    return render_template('index.html', users=allUsers, menu=menu)

# пользовательские альбомы - добавить редирект при совпадении ников (nickname==currentNick => redirect)
@app.route('/<string:nickname>/albums', methods=['GET'])
def get_user_albums(nickname):
    albums = get_all_albums_public(db, nickname)
    return render_template('user_albums.html',albums=albums, nickname=nickname, menu=menu)

# пользовательские фото - аналогично при совпадении текущего никнейма
@app.route('/<string:nickname>/albums/<int:album_id>', methods=['GET'])
def get_album_photos(nickname, album_id):
    photos = db.session.query(Photos).filter_by(album_id=album_id)
    album_name = db.session.query(Albums).filter_by(album_id=album_id, privacy=False).first().album_name
    return render_template('photos_in_album.html', album_id=album_id, nickname=nickname, photos=photos, menu=menu, album_name=album_name, toolbar=1)

# 
@app.route('/get_photos', methods=['GET'])
def getFotos():
    allPhotos = db.session.query(Photos).all()
    output = []
    for photo in allPhotos:
        currentPhoto = {}
        currentPhoto['description'] = photo.description
        currentPhoto['photo_url'] = photo.photo_url
        currentPhoto['likes'] = photo.like_counter
        output.append(currentPhoto)
    return jsonify(output)

app.run()

# @login_manager.user_loader
# def load_user(user_id):
#     print("load user")
#     user = UserLogin().fromDB(user_id, db, Users)
#     print(user)
#     return user