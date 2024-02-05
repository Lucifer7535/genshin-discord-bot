import enum

from utility.emoji import emoji


class Element(enum.Enum):
    CRYO = "Cryo"
    HYDRO = "Hydro"
    PYRO = "Pyro"
    ELECTRO = "Electro"
    GEO = "Geo"
    DENDRO = "Dendro"
    ANEMO = "Anemo"
    VOID = "None"

    def __str__(self) -> str:
        return emoji.elements.get(self.name, str(self.value))


class CostElement(str, enum.Enum):

    ENERGY = "GCG_COST_ENERGY"
    WHITE = "GCG_COST_DICE_SAME"
    BLACK = "GCG_COST_DICE_VOID"
    LEGEND = "GCG_COST_LEGEND"
    CRYO = "GCG_COST_DICE_CRYO"
    HYDRO = "GCG_COST_DICE_HYDRO"
    PYRO = "GCG_COST_DICE_PYRO"
    ELECTRO = "GCG_COST_DICE_ELECTRO"
    GEO = "GCG_COST_DICE_GEO"
    DENDRO = "GCG_COST_DICE_DENDRO"
    ANEMO = "GCG_COST_DICE_ANEMO"

    def __str__(self) -> str:
        return {
            "ENERGY": "ENERGY",
            "WHITE": "WHITE",
            "BLACK": "BLACK",
            "LEGEND": "LEGEND",
            "CRYO": "CRYO",
            "HYDRO": "HYDRO",
            "PYRO": "PYRO",
            "ELECTRO": "ELECTRO",
            "GEO": "GEO",
            "DENDRO": "DENDRO",
            "ANEMO": "ANEMO",
        }.get(self.name, "")
