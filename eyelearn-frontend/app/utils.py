from app .models import Incorrect_Character
from app import db
from flask_login import current_user

def checkForIncorrectCharacters(guess, word):
    for guessChar, wordChar in zip(guess, word):
        if guessChar != wordChar:
            incorrect_character = Incorrect_Character(class_id=current_user.current_class, user_id=current_user.user_id,
                                                      incorrect_letter=guessChar, correct_letter=wordChar)
            db.session.add(incorrect_character)
            db.session.commit()