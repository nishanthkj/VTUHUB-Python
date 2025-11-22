from pydantic import BaseModel

class SingleRequest(BaseModel):
    index_url: str
    usn: str


class RangeRequest(BaseModel):
    index_url: str
    start_usn: str
    end_usn: str
