from pydantic import BaseModel


class PhoneRead(BaseModel):
    id: int
    number: str

    class Config:
        from_attributes = True
