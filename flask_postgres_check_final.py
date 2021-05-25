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

# менеджинг списка альбомов
album_list_toolbar = {
    "Добавить альбом": "add_album"
}

# меню авторизированного пользователя - редактирование альбома
album_toolbar = {
    'Добавить фото': {
        'url': 'add_photo_to_album',
        'album_id': 1,
    },
    'Редактировать описание': {
        'url': 'change_album_description',
        'album_id': 1
    },
    'Приватность':{
        'url': 'change_privacy',
        'album_id': 1
    },
    'Удалить альбом': 'index',
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

# редактирование приватности альбома
@app.route('/myalbums/<int:album_id>/change_privacy', methods=['GET', 'POST'])
def change_privacy(album_id):
    album = db.session.query(Albums).filter_by(album_id=album_id).first()
    if request.method == 'POST':
        is_private = True if request.form.get('privacy') == 'on' else False
        album.privacy = is_private
        db.session.commit()
        return redirect(url_for('photos_of_current_user_album', album_id=album_id))
    else:
        if(current_user is not None):
            return render_template('change_privacy.html', nickname=current_user.nickname,
                menu=menu, album_id = album_id, album_privacy=album.privacy,
                album_name = album_toolbar['Добавить фото']['album_name'], 
                is_not_toolbar = True)
        else:
            flash('Анонимный пользователь', 'error')
            return redirect(url_for('index'))


# редактирование описания альбома
@app.route('/myalbums/<int:album_id>/change_album_description', methods=['GET', 'POST'])
def change_album_description(album_id):
    album = db.session.query(Albums).filter_by(album_id=album_id).first()
    if request.method == 'POST':
        if len(request.form['description']) > 0:
            album.description = request.form['description']
        else:
            album.description = None
        db.session.commit()
        return redirect(url_for('photos_of_current_user_album', album_id=album_id))
    else:
        if(current_user is not None):
            print(current_user)
            return render_template('change_description.html', nickname=current_user.nickname,
                menu=menu, album_id = album_id, album_description=album.description,
                album_name = album_toolbar['Добавить фото']['album_name'], 
                is_not_toolbar = True)
        else:
            flash('Анонимный пользователь', 'error')
            return redirect(url_for('index'))

# добавление фото в альбом пользователя
@app.route('/myalbums/<int:album_id>/add_photo_to_album', methods=['GET', 'POST'])
def add_photo_to_album(album_id):
    if request.method == 'POST':
        if len(request.form['photo_url']) > 0:
            photo_args = {
                'photo_url': request.form['photo_url'],
                'description':request.form['description'] if len(request.form['description']) > 0 else None,
                'album_id': album_id,
            }

            photo = Photos(**photo_args)
            print(photo.photo_url)

            db.session.add(photo)
            print('добавил')
            db.session.commit()
            print('закомитил')
            flash(f'Поздравляем, фото добвалено!', 'success')
            return redirect(url_for('photos_of_current_user_album', album_id=album_id))
        else:
            flash('Неправильно введены данные: введите ссылку на фото', 'error')
    else:
        if(current_user is not None):
            print(current_user)
            return render_template('add_photo.html', nickname=current_user.nickname,
                menu=menu, album_id = album_id, album_name = album_toolbar['Добавить фото']['album_name'], 
                is_not_toolbar = True)
        else:
            flash('Анонимный пользователь', 'error')
            return redirect(url_for('index'))

# альбомы пользователя
@app.route('/myalbums', methods=['GET'])
def my_albums():
    if(current_user is not None):
        print(current_user)
        albums = db.session.query(Albums).filter_by(user_id=current_user.user_id)
        return render_template(
            'user_albums.html',albums=albums, 
            nickname=current_user.nickname, menu=menu, 
            album_list_toolbar = album_list_toolbar, is_not_toolbar = False, 
            albums_length = albums.count())
    else:
        flash('что-то не то', 'error')
        return redirect(url_for('index'))

# альбомы пользователя
@app.route('/add_album', methods=['GET', 'POST'])
def add_album():
    if request.method == 'POST':
        if len(request.form['album_name']) > 5:
            album_args = {
                'album_name': request.form['album_name'],
                'description':request.form['description'] if len(request.form['description']) > 0 else None,
                'user_id': current_user.user_id,
                'privacy': True if request.form.get('privacy') == 'on' else False,
            }

            album = Albums(**album_args)
            print(album.album_name)

            db.session.add(album)
            print('добавил')
            db.session.commit()
            print('закомитил')
            flash(f'Поздравляем, альбом "{album.album_name}" создан!', 'success')
            return redirect(url_for('my_albums'))
        else:
            flash('Неправильно введены данные: название альбома должно содержать не менее 6 символов', 'error')
    else:
        if(current_user is not None):
            print(current_user)
            return render_template('add_album.html', nickname=current_user.nickname, menu=menu, is_not_toolbar = True)
        else:
            flash('Анонимный пользователь', 'error')
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

    return render_template('authorization.html', menu=menu, is_not_toolbar = True)

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
    

    return render_template('register.html', menu=menu, is_not_toolbar = True)

@app.route('/test', methods=['GET'])
def test():
    return {
        'test':'test1'
    }

# главная страница
@app.route('/')
def index():
    allUsers = db.session.query(Users).all()
    return render_template('index.html', users=allUsers, menu=menu, is_not_toolbar = True)

# пользовательские альбомы - добавить редирект при совпадении ников (nickname==currentNick => redirect)
@app.route('/<string:nickname>/albums', methods=['GET'])
def get_user_albums(nickname):
    global current_user
    if current_user is not None and nickname == current_user.nickname:
        return redirect(url_for('my_albums'))
    else:
        albums = get_all_albums_public(db, nickname)
        return render_template('user_albums.html',albums=albums, nickname=nickname,
         menu=menu, is_not_toolbar = True, albums_length = len(albums))

# пользовательские фото - аналогично при совпадении текущего никнейма
@app.route('/<string:nickname>/albums/<int:album_id>', methods=['GET'])
def get_album_photos(nickname, album_id):
    if current_user is not None:
        return redirect(url_for('photos_of_current_user_album', album_id=album_id))
    photos = db.session.query(Photos).filter_by(album_id=album_id)
    album_name = db.session.query(Albums).filter_by(album_id=album_id).first().album_name
    return render_template('photos_in_album.html', album_id=album_id, nickname=nickname, photos=photos,
    menu=menu, album_name=album_name, is_not_toolbar = True)

@app.route('/myalbums/<int:album_id>', methods=['GET'])
def photos_of_current_user_album(album_id):
    if current_user is not None:
        for key in album_toolbar.keys():
            if 'album_id' in album_toolbar[key]:
                album_toolbar[key]['album_id'] = album_id
        photos = db.session.query(Photos).filter_by(album_id=album_id)
        album_name = db.session.query(Albums).filter_by(album_id=album_id).first().album_name
        album_toolbar['Добавить фото']['album_name'] = album_name
        return render_template('photos_in_album.html', album_id=album_id, nickname=current_user.nickname, photos=photos,
        menu=menu, album_name=album_name, album_toolbar=album_toolbar, is_not_toolbar = False)
    

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