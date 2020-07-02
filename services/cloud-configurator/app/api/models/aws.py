from pydantic import BaseModel

class Account(BaseModel):
    name: str
    email: str