from pydantic import BaseModel, EmailStr,  Field
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: Optional[EmailStr] =None
    full_name: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Review Schemas ---

class ReviewBase(BaseModel):
    rating: int = Field(..., gt=0, lt=6, description="Rating from 1 to 5")
    comment: Optional[str] = None
    product_id: int
    user_id: int

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True # Pydantic V2 (旧版是 orm_mode = True)

# --- Product Schemas ---

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    reviews: List[Review] = [] # 在读取单个商品时，也返回其所有评价

    class Config:
        from_attributes = True # Pydantic V2 (旧版是 orm_mode = True)

class ProductSearchResult(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

    class Config:
        from_attributes = True

# !! 新增这个 ProductUpdate 模型 !!
class ProductUpdate(BaseModel):
    # 更新时所有字段都应该是可选的
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)

