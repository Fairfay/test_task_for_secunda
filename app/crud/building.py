from app.models.building import Building
from app.crud.base import CRUDBase


class BuildingCRUD(CRUDBase):
    """
    CRUD Для Зданий.
    """
    def __init__(self):
        super().__init__(Building)


building_crud = BuildingCRUD()
