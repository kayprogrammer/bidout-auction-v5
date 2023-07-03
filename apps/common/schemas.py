from pydantic import BaseModel as BaseModel


class ResponseSchema(BaseModel):
    status: str = "success"
    message: str
