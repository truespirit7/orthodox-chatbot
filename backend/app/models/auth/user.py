  
from sqlalchemy import Column, String, DateTime, Boolean  
from sqlalchemy.sql import func  
from tkhelper.models.base import BaseModel  
from typing import Dict, Any  
  
class User(BaseModel):  
    __tablename__ = "users"  
      
    user_id = Column(String(50), primary_key=True)  
    email = Column(String(255), unique=True, nullable=False)  
    password_hash = Column(String(255), nullable=False)  
    full_name = Column(String(255), nullable=True)  
    is_active = Column(Boolean, default=True)  
    created_at = Column(DateTime, server_default=func.now())  
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  
      
    def to_response_dict(self) -> Dict[str, Any]:  
        return {  
            "user_id": self.user_id,  
            "email": self.email,  
            "full_name": self.full_name,  
            "is_active": self.is_active,  
            "created_at": self.created_at.isoformat() if self.created_at else None,  
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,  
        }