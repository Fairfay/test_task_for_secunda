from app.models.activity import Activity
from app.crud.base import CRUDBase


class ActivityCRUD(CRUDBase):
    """
    CRUD Для Активностей.
    """
    def __init__(self):
        super().__init__(Activity)


activity_crud = ActivityCRUD()
