class AlbumsPublic():
    def __init__(self, raw_item):
        self.nickname = raw_item[0]
        self.album_id = raw_item[1]
        self.album_name = raw_item[2]
        self.description = raw_item[3]
        self.photo_count = raw_item[4]
        self.privacy = raw_item[5]
        self.photo_cover_id = raw_item[6]
        self.photo_cover_url = 'https://images.unsplash.com/source-404?fit=crop&fm=jpg&h=800&q=60&w=1200'
            
    def __repr__(self):
        return f"<{self.album_name} : '{self.description}', приватность: {self.privacy}>"

def get_all_albums_public(db, nickname):
    albums_raw = db.engine.execute(f"select * from album_info_public where nickname = '{nickname}'")
    albums = []
    for album in albums_raw:
        albums.append(AlbumsPublic(album))
    return albums