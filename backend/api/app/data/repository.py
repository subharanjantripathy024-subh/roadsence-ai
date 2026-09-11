from typing import List, Optional
from app.models.domain import DamageInstance, M1Detection
from app.data.adapters import M1Adapter, M2Adapter
from app.config import settings


class DataRepository:
    def __init__(self):
        self._m1_data: List[M1Detection] = []
        self._m2_data: List[DamageInstance] = []
        self._is_loaded: bool = False

    def load_data(
        self,
        m1_path: Optional[str] = None,
        m2_path: Optional[str] = None
    ) -> bool:
        """Load M1 and M2 data independently."""

        m1_path = m1_path or settings.M1_DATA_PATH
        m2_path = m2_path or settings.M2_DATA_PATH

        try:
            # Load M1 data
            new_m1_data = M1Adapter.load_csv(m1_path)

            # M2 is optional for now
            try:
                new_m2_data = M2Adapter.load_geojson(m2_path)
            except Exception as e:
                print(f"[INFO] M2 data unavailable: {e}")
                new_m2_data = []

            if isinstance(new_m1_data, list):
                self._m1_data = new_m1_data
                self._m2_data = new_m2_data
                self._is_loaded = True
                return True

            return False

        except Exception as e:
            print(f"Failed to load M1 data: {e}")
            return False

    def get_all_damages(self) -> List[DamageInstance]:
        if not self._is_loaded:
            self.load_data()
        return self._m2_data

    def get_damage_by_id(
        self,
        damage_id: str
    ) -> Optional[DamageInstance]:
        if not self._is_loaded:
            self.load_data()

        for d in self._m2_data:
            if d.damage_id == damage_id:
                return d

        return None

    def get_damages_by_priority(self) -> List[DamageInstance]:
        if not self._is_loaded:
            self.load_data()

        return sorted(
            self._m2_data,
            key=lambda x: x.priority
        )


# Singleton instance
repository = DataRepository()
