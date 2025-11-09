from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency for external configs
    yaml = None


@dataclass
class CropInfo:
    temperature_range: Optional[Tuple[Optional[float], Optional[float]]]
    water_l: Optional[float]
    fertilizer_family: Optional[str]


@dataclass
class ChemicalInfo:
    volume_l: float
    targets: List[str]


class KnowledgeBase:
    def __init__(self, data: Dict):
        self._data = data
        self.crops: Dict[str, CropInfo] = {}
        for crop_name, info in data.get("CROPS", {}).items():
            temp = info.get("temp")
            if temp:
                temp_range = (float(temp[0]), float(temp[1]))
            else:
                temp_range = (None, None)
            water = info.get("water")
            water_l = float(water) if water is not None else None
            fert = info.get("fert")
            self.crops[crop_name.upper()] = CropInfo(temp_range, water_l, fert)
        self.pests: Dict[str, Dict[str, ChemicalInfo]] = {}
        for category, chemicals in data.get("PESTS", {}).items():
            normalized = {}
            for chem_class, chem_info in chemicals.items():
                normalized[chem_class.upper()] = ChemicalInfo(
                    volume_l=float(chem_info["volume_l"]),
                    targets=[target.upper() for target in chem_info.get("targets", [])],
                )
            self.pests[category.upper()] = normalized
        self.genes: Dict[str, str] = {
            gene.upper(): description
            for gene, description in data.get("GENES", {}).items()
        }

    @classmethod
    def load_from_file(cls, path: Path) -> "KnowledgeBase":
        if yaml is None:
            raise RuntimeError("PyYAML is required to load external knowledge files")
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return cls(data)

    @classmethod
    def load_default(cls) -> "KnowledgeBase":
        from . import resources

        return cls(resources.DEFAULT_KNOWLEDGE)

    def get_crop(self, crop_name: Optional[str]) -> Optional[CropInfo]:
        if not crop_name:
            return None
        return self.crops.get(crop_name.upper())

    def get_pest_category(self, crop_name: Optional[str]) -> str:
        if crop_name and "ВИНОГРАД" in crop_name.upper():
            return "ВИНОГРАД"
        return "ОБЩИЕ"

    def find_chemical(self, crop_name: Optional[str], parasite_name: str) -> Optional[Tuple[str, ChemicalInfo]]:
        parasite_normalized = parasite_name.upper()
        category = self.get_pest_category(crop_name)
        for chem_class, info in self.pests.get(category, {}).items():
            if any(target in parasite_normalized for target in info.targets):
                return chem_class, info
        # fallback search across all categories
        for chem_class, info in self.pests.get("ОБЩИЕ", {}).items():
            if any(target in parasite_normalized for target in info.targets):
                return chem_class, info
        return None

    def gene_effect(self, gene: str) -> Optional[str]:
        return self.genes.get(gene.upper())


DEFAULT_KNOWLEDGE = {
    "CROPS": {
        "ПОМИДОРЫ": {"temp": (12, 15), "water": 5, "fert": "МИНЕРАЛЬНЫЕ"},
        "ТЫКВА": {"temp": (12, 17), "water": 12, "fert": "АЗОТНЫЕ"},
        "КУКУРУЗА": {"temp": (-2, 24), "water": 5, "fert": "АЗОТНЫЕ"},
        "ЛУК РЕПЧАТЫЙ": {"temp": (10, 20), "water": 7, "fert": "АЗОТНЫЕ"},
        "СВЕКЛА": {"temp": (5, 18), "water": 6, "fert": "КАЛИЙНЫЕ"},
        "ПЕРЕЦ": {"temp": (15, 27), "water": 3, "fert": "МИНЕРАЛЬНЫЕ"},
        "АРБУЗ": {"temp": (18, 30), "water": 8, "fert": "МИНЕРАЛЬНЫЕ"},
        "ОГУРЦЫ": {"temp": (15, 30), "water": 4, "fert": "ФОСФОРНЫЕ"},
        "БАКЛАЖАНЫ": {"temp": (15, 28), "water": 10, "fert": "МИНЕРАЛЬНЫЕ"},
        "КАРТОФЕЛЬ": {"temp": (5, 25), "water": 3, "fert": "ФОСФОРНЫЕ"},
        "МОРКОВЬ": {"temp": (6, 25), "water": 6, "fert": "ФОСФОРНЫЕ"},
        "РЕДИСКА": {"temp": (-2, 20), "water": 7, "fert": "КАЛИЙНЫЕ"},
        "КАПУСТА": {"temp": (5, 20), "water": 8, "fert": "КАЛИЙНЫЕ"},
        "ЧЕСНОК": {"temp": (8, 27), "water": 5, "fert": "ФОСФОРНЫЕ"},
        "ВИНОГРАД БЕЛЫЙ": {"temp": None, "water": 3, "fert": "МИНЕРАЛЬНЫЕ"},
        "ВИНОГРАД РОЗОВЫЙ": {"temp": None, "water": 4, "fert": "АЗОТНЫЕ"},
    },
    "GENES": {
        "X": "приманивает больше паразитов",
        "W": "требует больше воды",
        "Y": "увеличивает количество урожая",
        "G": "ускоряет рост растения",
        "H": "увеличивает здоровье растения",
    },
    "PESTS": {
        "ОБЩИЕ": {
            "БИОЛОГИЧЕСКИЕ": {
                "volume_l": 2.1,
                "targets": ["ТЛЯ", "ГОЛЫЕ СЛИЗНИ", "КОЛОРАДСКИЙ ЖУК"],
            },
            "СИСТЕМНЫЕ": {
                "volume_l": 1.1,
                "targets": ["ЖУК-ЩЕЛКУН", "КРАВЧИК-ГОЛОВАЧ"],
            },
            "КИШЕЧНЫЕ": {
                "volume_l": 4.1,
                "targets": ["МЕДВЕДКА", "ПРОВОЛОЧНИК", "ГАЛЛОВАЯ НЕМАТОДА"],
            },
            "КОНТАКТНЫЕ": {
                "volume_l": 3.1,
                "targets": ["ТРИПС", "ПАУТИИННЫЙ КЛЕЩ"],
            },
        },
        "ВИНОГРАД": {
            "БИОЛОГИЧЕСКИЕ": {
                "volume_l": 2.1,
                "targets": ["ЦИКАДЫ", "СОСАРЬ", "СКОСАРЬ"],
            },
            "СИСТЕМНЫЕ": {
                "volume_l": 1.1,
                "targets": ["ДЫМЧАТАЯ ПЯДЕНИЦА", "ВИНОГРАДНЫЙ ЗУДЕНЬ"],
            },
            "КИШЕЧНЫЕ": {
                "volume_l": 4.1,
                "targets": ["ВОЙЛОЧНЫЙ КЛЕЩ"],
            },
            "КОНТАКТНЫЕ": {
                "volume_l": 3.1,
                "targets": ["ЧЕРВЕЦЫ", "ФИЛЛОКСЕРА"],
            },
        },
    },
}
