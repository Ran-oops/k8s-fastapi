from sqlalchemy.orm import Session
from app import models, schemas


def get_user(db: Session, user_id: int):
    # 类似 Django 的 Users.objects.get(id=user_id)
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    # 类似 Django 的 Users.objects.filter(email=email).first()
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    # 类似 Django 的 Users.objects.all()[skip:skip+limit]
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    # 类似 Django 的 Users.objects.create(...)
    user_data = user.model_dump()
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    # 类似 Django 的 user = Users.objects.get(id=user_id)
    #         user.email = new_email; user.save()
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None

    # 仅包含实际提供的字段，排除所有未设置的默认值字段
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    # 作用是从数据库重新加载该对象的当前状态
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    # 类似 Django 的 Users.objects.filter(id=user_id).delete()
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()
    return True





























