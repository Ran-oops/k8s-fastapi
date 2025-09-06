# app/crud.py
from sqlalchemy.orm import Session
import logging
from . import models, schemas

logger = logging.getLogger(__name__)

# --- Product CRUD ---
def get_product(db: Session, product_id: int):
    logger.debug("Fetching product from database", extra={
        "event": "fetching_product",
        "product_id": product_id
    })
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        logger.info("Product found in database", extra={
            "event": "product_found",
            "product_id": product_id
        })
    else:
        logger.info("Product not found in database", extra={
            "event": "product_not_found",
            "product_id": product_id
        })
    return product


def create_product(db: Session, product: schemas.ProductCreate):
    logger.info("Creating product in database", extra={
        "event": "creating_product",
        "product_name": product.name
    })
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    logger.info("Product created in database", extra={
        "event": "product_created",
        "product_id": db_product.id
    })
    return db_product


# --- User CRUD ---
def get_user(db: Session, user_id: int):
    logger.debug("Fetching user from database", extra={
        "event": "fetching_user",
        "user_id": user_id
    })
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        logger.info("User found in database", extra={
            "event": "user_found",
            "user_id": user_id
        })
    else:
        logger.info("User not found in database", extra={
            "event": "user_not_found",
            "user_id": user_id
        })
    return user


def get_user_by_email(db: Session, email: str):
    logger.debug("Fetching user by email from database", extra={
        "event": "fetching_user_by_email",
        "email": email
    })
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        logger.info("User found by email in database", extra={
            "event": "user_found_by_email",
            "email": email,
            "user_id": user.id
        })
    else:
        logger.info("User not found by email in database", extra={
            "event": "user_not_found_by_email",
            "email": email
        })
    return user


def get_users(db: Session, skip: int = 0, limit: int = 100):
    logger.debug("Fetching users list from database", extra={
        "event": "fetching_users_list",
        "skip": skip,
        "limit": limit
    })
    users = db.query(models.User).offset(skip).limit(limit).all()
    logger.info("Users list fetched from database", extra={
        "event": "users_list_fetched",
        "count": len(users),
        "skip": skip,
        "limit": limit
    })
    return users


def create_user(db: Session, user: schemas.UserCreate):
    logger.info("Creating user in database", extra={
        "event": "creating_user",
        "user_email": user.email
    })
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info("User created in database", extra={
        "event": "user_created",
        "user_id": db_user.id,
        "user_email": db_user.email
    })
    return db_user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    logger.info("Updating user in database", extra={
        "event": "updating_user",
        "user_id": user_id
    })
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
        logger.info("User updated in database", extra={
            "event": "user_updated",
            "user_id": user_id
        })
    else:
        logger.warning("User not found for update in database", extra={
            "event": "user_not_found_for_update",
            "user_id": user_id
        })
    return db_user


def delete_user(db: Session, user_id: int):
    logger.info("Deleting user from database", extra={
        "event": "deleting_user",
        "user_id": user_id
    })
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        logger.info("User deleted from database", extra={
            "event": "user_deleted",
            "user_id": user_id
        })
        return True
    else:
        logger.warning("User not found for deletion in database", extra={
            "event": "user_not_found_for_deletion",
            "user_id": user_id
        })
        return False


# --- Review CRUD ---
def create_review(db: Session, review: schemas.ReviewCreate):
    logger.info("Creating review in database", extra={
        "event": "creating_review",
        "product_id": review.product_id,
        "user_id": review.user_id,
        "rating": review.rating
    })
    db_review = models.Review(**review.model_dump())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    logger.info("Review created in database", extra={
        "event": "review_created",
        "review_id": db_review.id,
        "product_id": review.product_id,
        "user_id": review.user_id
    })
    return db_review