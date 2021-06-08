from flask import Flask, jsonify, render_template, \
url_for, request, flash, redirect, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from utils.custom_orm import get_all_albums_public, \
get_all_photos_of_user, get_all_albums
from werkzeug.security import generate_password_hash, check_password_hash
from UserLogin import UserLogin
import re

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] \
= "postgresql://postgres:koij890hgf@localhost:5433/postgres"
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
    'Ввести код': 'enter_album_code',
    'Вход': 'authorize' 
}

menu_in = menu

# главное меню после входа
menu_out = {
    'Главная': 'index',
    'Ввести код': 'enter_album_code',
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
    'Удалить альбом': {
        'url': 'delete_album',
        'album_id': 1
    },
}

# меню авторизированного пользователя - редактирование фото
photo_toolbar = {
    'Добавить'
}

current_user = None
secret_album = None
is_authorized = False

def get_auth_user_like(photo_id):
    if current_user is None:
        return True
    like = db.session.query(Likes)\
        .filter_by(photo_id=photo_id, user_id = current_user.user_id)\
        .first()
    return like is not None

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

def set_photo_action_menu(photo_id):
    photo = db.session.query(Photos).filter_by(photo_id=photo_id).first()
    if request.form['btn'] == 'like_a_photo':
        db.session.execute(f"call toggle_like({current_user.user_id}, {photo_id});")
        db.session.commit()
    elif request.form['btn'] == 'change_description':
        description = request.form['description']
        if len(description) > 0:
            photo.description = description
            db.session.commit()
        else:
            flash('Неправильно введены данные: введите ссылку на фото', 'error')
    elif request.form['btn'] == 'delete_photo':
        db.session.delete(photo)
        db.session.commit()

@app.route('/review', methods=['GET', 'POST'])
def add_review():
    if request.method == 'POST':
        if len(request.form['full_name']) < 10:
            flash('ФИО должно составлять больше 10 символов')
            return render_template('add_review.html', menu=menu, is_not_toolbar = True)
        if len(request.form['review_text']) < 1:
            flash('[Текст отзыва] Напишите хотя бы один символ')
            return render_template('add_review.html', menu=menu, is_not_toolbar = True)
        if re.match(r'[^1-5]', request.form['rating']):
            flash('[Оценка] Введите правильно оценку (от 1 до 5)')
            return render_template('add_review.html', menu=menu, is_not_toolbar = True)
        review = Reviews(
            full_name = request.form['full_name'],
            review_text = request.form['review_text'],
            album_id = secret_album.album_id,
            rating = int(request.form['rating'])
        )
        try:
            db.session.add(review)
            db.session.commit()
        except:
            flash('Уже есть отзыв')
            user = db.session.query(Users).filter_by(user_id=secret_album.user_id).first()
            photos = db.session.query(Photos).filter_by(album_id=secret_album.album_id)
            review = db.session.query(Reviews).filter_by(album_id=secret_album.album_id).first()
            return render_template('photos_in_album.html', album_id=secret_album.album_id, 
            nickname=user.nickname, photos=photos, is_album_from_code = True,
            menu=menu, album_name=secret_album.album_name, review=review, 
            is_customer=is_customer, is_not_toolbar = True)
        is_customer = False
        if current_user is not None:
            is_customer = secret_album.user_id != current_user.user_id
        user = db.session.query(Users).filter_by(user_id=secret_album.user_id).first()
        photos = db.session.query(Photos).filter_by(album_id=secret_album.album_id)
        review = db.session.query(Reviews).filter_by(album_id=secret_album.album_id).first()
        return render_template('photos_in_album.html', album_id=secret_album.album_id, 
        nickname=user.nickname, photos=photos, is_album_from_code = True,
        menu=menu, album_name=secret_album.album_name, 
        review=review, is_customer=is_customer, is_not_toolbar = True)

    else:
        if current_user is not None and secret_album.user_id == current_user.user_id:
            flash('Автор не может оставлять сам себе отзыв')
            return redirect(url_for('index'))
        else:
            return render_template('add_review.html', menu=menu, is_not_toolbar = True)
            

# получение альбома по коду
@app.route('/album_from_code', methods=['GET', 'POST'])
def album_from_code():
    is_customer = True
    if current_user is not None:
        is_customer = secret_album.user_id != current_user.user_id
    if secret_album is None:
        return redirect(url_for('index'))
    else:
        user = db.session.query(Users).filter_by(user_id=secret_album.user_id).first()
        photos = db.session.query(Photos).filter_by(album_id=secret_album.album_id)
        review = db.session.query(Reviews).filter_by(album_id=secret_album.album_id).first()
        return render_template('photos_in_album.html', album_id=secret_album.album_id, 
        nickname=user.nickname, photos=photos, 
        review=review, is_album_from_code = True,
        menu=menu, album_name=secret_album.album_name, 
        is_customer=is_customer, is_not_toolbar = True)
    

# ввод кода
@app.route('/album_code', methods=['GET', 'POST'])
def enter_album_code():
    global secret_album
    if request.method == 'POST':
        album = db.session.query(Albums).filter_by(album_code=request.form['code']).first()
        if album is not None:
            secret_album = album
            return redirect(url_for('album_from_code'))
        flash('Неверный код альбома', 'error')

    return render_template('album_code.html', menu=menu, is_not_toolbar = True)

# фото - редирект при совпадении текущего никнейма
@app.route('/<string:nickname>/albums/<int:album_id>/<int:photo_id>', methods=['GET', 'POST'])
def get_photo(nickname, album_id, photo_id):
    if current_user is not None and nickname == current_user.nickname:
        return redirect(
            url_for(
                'get_photo_current_user', album_id=album_id, photo_id=photo_id),
                code=307 if request.method == 'POST' else 302
            )
    if request.method == 'POST':
        if request.form['btn'] == 'back':
            if album_id == secret_album.album_id and \
                (current_user == None or secret_album.user_id != current_user.user_id):
                    return redirect(url_for('album_from_code'))
            return redirect(url_for('photos_of_current_user_album', album_id=album_id))
        if nickname != current_user.nickname:
            set_photo_action_menu(photo_id)
            return redirect(url_for('get_photo', album_id=album_id, 
            photo_id=photo_id, nickname = nickname))
    is_auth = current_user is not None
    photo = db.session.query(Photos).filter_by(photo_id=photo_id).first()
    album_name = db.session.query(Albums).filter_by(album_id=album_id).first().album_name
    return render_template('photo.html', album_id=album_id, nickname=nickname, photo=photo,
    menu=menu, album_name=album_name, is_auth=is_auth, 
    is_not_toolbar = True, get_auth_user_like=get_auth_user_like)

@app.route('/myalbums/<int:album_id>/<int:photo_id>', methods=['GET', 'POST'])
def get_photo_current_user(album_id, photo_id):
    if current_user is None:
        flash('Анонимный пользователь', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        set_photo_action_menu(photo_id)
        if request.form['btn'] == 'delete_photo' or request.form['btn'] == 'back':
            return redirect(url_for('photos_of_current_user_album', album_id=album_id))
        return redirect(url_for('get_photo_current_user', album_id=album_id, photo_id=photo_id))
    else:
        photo = db.session.query(Photos).filter_by(photo_id=photo_id).first()
        album_name = db.session.query(Albums).filter_by(album_id=album_id).first().album_name
        return render_template('photo.html', album_id=album_id, 
        nickname=current_user.nickname, photo=photo,
        menu=menu, album_name=album_name, is_auth = True, 
        is_not_toolbar = True, photo_menu = True,
        get_auth_user_like=get_auth_user_like)

# удаление альбома
@app.route('/myalbums/<int:album_id>/delete_album', methods=['GET', 'POST'])
def delete_album(album_id):
    if current_user is None:
        flash('Анонимный пользователь', 'error')
        return redirect(url_for('index'))
    album = db.session.query(Albums).filter_by(album_id=album_id).first()
    if request.method == 'POST':
        confirmed = True if request.form.get('confirmation') == 'on' else False
        if(confirmed):
            db.session.delete(album)
            db.session.commit()
            return redirect(url_for('my_albums'))
        else:
            return redirect(url_for('photos_of_current_user_album', 
            album_id=album_id))
    else:
        if(current_user is not None):
            return render_template('delete_confirm.html', 
            nickname=current_user.nickname,
                menu=menu, album_id = album_id,
                album_name = album_toolbar['Добавить фото']['album_name'], 
                is_not_toolbar = True)

# редактирование приватности альбома
@app.route('/myalbums/<int:album_id>/change_privacy', methods=['GET', 'POST'])
def change_privacy(album_id):
    if current_user is None:
        flash('Анонимный пользователь', 'error')
        return redirect(url_for('index'))
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


# редактирование описания альбома
@app.route('/myalbums/<int:album_id>/change_album_description', methods=['GET', 'POST'])
def change_album_description(album_id):
    if current_user is None:
        flash('Анонимный пользователь', 'error')
        return redirect(url_for('index'))
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

# добавление фото в альбом пользователя
@app.route('/myalbums/<int:album_id>/add_photo_to_album', methods=['GET', 'POST'])
def add_photo_to_album(album_id):
    if current_user is None:
        flash('Анонимный пользователь', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        if len(request.form['photo_url']) > 0:
            photo_args = {
                'photo_url': request.form['photo_url'],
                'description':request.form['description'] \
                if len(request.form['description']) > 0 else None,
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

# альбомы пользователя зареганного
@app.route('/myalbums', methods=['GET'])
def my_albums():
    if(current_user is not None):
        print(current_user)
        albums = get_all_albums(db, current_user.nickname)
        return render_template(
            'user_albums.html',albums=albums, 
            nickname=current_user.nickname, menu=menu, 
            album_list_toolbar = album_list_toolbar, is_not_toolbar = False, 
            albums_length = len(albums))
    else:
        flash('Анонимный пользователь', 'error')
        return redirect(url_for('index'))

# альбомы пользователя
@app.route('/add_album', methods=['GET', 'POST'])
def add_album():
    if current_user is None:
        flash('Анонимный пользователь', 'error')
        return redirect(url_for('index'))
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
            flash('Неправильно введены данные: название \
            альбома должно содержать не менее 6 символов', 'error')
    else:
        if(current_user is not None):
            print(current_user)
            return render_template('add_album.html', 
            nickname=current_user.nickname, menu=menu, 
            is_not_toolbar = True)

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
            is_valid_nick = db.session.execute(f"select * from is_nick_valid('{request.form['nick']}')")\
            .fetchone()[0]
            print(is_valid_nick)
            if not is_valid_nick:
                flash('Псевдоним уже занят!')
                return render_template('register.html', menu=menu, is_not_toolbar = True)

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
                flash('Не удалось зарегаться \
                (username уже есть в базе или пароль > 30 символов или телефон не российский)', 'error')
        else:
            flash('Неправильно введены данные: username должен быть больше 4 символов,\
             пароль должен быть больше 8 символов', 'error')
    

    return render_template('register.html', menu=menu, is_not_toolbar = True)

# главная страница
@app.route('/')
def index():
    allUsers = db.session.query(Users).all()
    return render_template('index.html', users=allUsers, menu=menu, is_not_toolbar = True)

@app.route('/<string:nickname>/albums', methods=['GET'])
def get_user_albums(nickname):
    global current_user
    if current_user is not None and nickname == current_user.nickname:
        return redirect(url_for('my_albums'))
    else:
        albums = get_all_albums_public(db, nickname)
        return render_template('user_albums.html',albums=albums, nickname=nickname,
        menu=menu, is_not_toolbar = True, albums_length = len(albums))

@app.route('/<string:nickname>/albums/all_photos', methods=['GET'])
def all_user_photos(nickname):
    if current_user is not None and nickname == current_user.nickname:
        return redirect(url_for('all_photos_of_current_user'))
    photos = get_all_photos_of_user(db, nickname)
    return render_template('all_user_photos.html', nickname=nickname, photos=photos,
    menu=menu, album_name="Все фото", is_not_toolbar = True)

@app.route('/myalbums/all_photos', methods=['GET'])
def all_photos_of_current_user():
    photos = get_all_photos_of_user(db, current_user.nickname)
    return render_template('all_user_photos.html', nickname=current_user.nickname, photos=photos,
    menu=menu, album_name="Все фото", is_not_toolbar = True)

# пользовательские фото - аналогично при совпадении текущего никнейма
@app.route('/<string:nickname>/albums/<int:album_id>', methods=['GET'])
def get_album_photos(nickname, album_id):
    if current_user is not None and nickname == current_user.nickname:
        return redirect(url_for('photos_of_current_user_album', album_id=album_id))
    photos = db.session.query(Photos).filter_by(album_id=album_id)
    album_name = db.session.query(Albums).filter_by(album_id=album_id).first().album_name
    review = db.session.query(Reviews).filter_by(album_id=album_id).first()
    return render_template('photos_in_album.html', album_id=album_id, nickname=nickname, photos=photos,
    menu=menu, album_name=album_name, review=review, is_not_toolbar = True)

@app.route('/myalbums/<int:album_id>', methods=['GET'])
def photos_of_current_user_album(album_id):
    if current_user is not None:
        for key in album_toolbar.keys():
            if 'album_id' in album_toolbar[key]:
                album_toolbar[key]['album_id'] = album_id
        photos = db.session.query(Photos).filter_by(album_id=album_id)
        album = db.session.query(Albums).filter_by(album_id=album_id).first()
        review = db.session.query(Reviews).filter_by(album_id=album_id).first()
        album_toolbar['Добавить фото']['album_name'] = album.album_name
        return render_template('photos_in_album.html', album_id=album_id, 
        nickname=current_user.nickname, photos=photos,
        menu=menu, review=review, album_code=f'(код: {album.album_code})', 
        album_name=album.album_name, album_toolbar=album_toolbar, is_not_toolbar = False)
    else:
        flash('Анонимный пользователь', 'error')
        return redirect(url_for('index'))
    

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
