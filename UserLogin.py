class UserLogin():
    def fromDB(self, user_id, db, Users):
        self.__user = db.session.query(Users).filter_by(user_id=user_id).first()
        return self
    
    def create(self, user):
        self.__user = user
        return self
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__user.user_id)