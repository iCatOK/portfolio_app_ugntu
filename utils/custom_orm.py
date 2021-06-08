class AlbumsPublic():
    def __init__(self, raw_item):
        self.nickname = raw_item[0]
        self.album_id = raw_item[1]
        self.album_name = raw_item[2]
        self.description = raw_item[3]
        self.photo_count = raw_item[4]
        self.privacy = raw_item[5]
        self.photo_cover_url= raw_item[6]

        if self.photo_cover_url is None:
            self.photo_cover_url = 'https://images.unsplash.com/source-404?fit=crop&fm=jpg&h=800&q=60&w=1200'
            
    def __repr__(self):
        return f"<{self.album_name} : '{self.description}', приватность: {self.privacy}>"

class Photos():
    def __init__(self, raw_item):
        self.photo_id = raw_item[0]
        self.description = raw_item[1]
        self.photo_url = raw_item[2]
        self.album_id = raw_item[3]
        self.like_counter = raw_item[4]
            
    def __repr__(self):
        return f"<Фото {self.photo_id} : '{self.description}', лайки: {self.like_counter}>"

def get_all_albums_public(db, nickname):
    albums_raw = db.engine.execute(f"select * from album_info_public where nickname = '{nickname}'")
    albums = [AlbumsPublic(album) for album in albums_raw]
    return albums

def get_all_photos_of_user(db, nickname):
    photos_raw = db.session.execute(f"select * from all_user_photos('{nickname}');")
    photos = [Photos(photo) for photo in photos_raw]
    return photos

def get_all_albums(db, nickname):
    albums_raw = db.engine.execute(f"select * from get_albums('{nickname}')")
    albums = [AlbumsPublic(album) for album in albums_raw]
    return albums