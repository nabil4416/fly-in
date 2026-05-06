"""Zone model for the Fly-in drone simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ZoneType(str, Enum):
    """Types de zones avec valeurs string pour le parseur."""

    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class ZoneCategory(str, Enum):
    """Catégories de zones provenant du fichier d'entrée."""

    START_HUB = "start_hub"
    END_HUB = "end_hub"
    HUB = "hub"


@dataclass(frozen=True)
class Zone:
    """Représente une zone du graphe utilisée par la simulation de drones.

    Attributes:
        name: Identifiant unique de la zone.
        x: Coordonnée X dans le réseau.
        y: Coordonnée Y dans le réseau.
        zone_type: Type de zone (normal, restricted, priority, blocked).
        category: Catégorie spéciale (start_hub, end_hub ou hub).
        max_drones: Nombre maximum de drones simultanés dans cette zone.
        color: Couleur optionnelle pour la visualisation.
        metadata: Métadonnées extensibles pour usage futur.

    Example:
        >>> start = Zone("hub_depart", 0, 0, ZoneType.NORMAL, ZoneCategory.START_HUB)
        >>> blocked = Zone("obstacle1", 3, 4, ZoneType.BLOCKED)
        >>> corridor = Zone("couloir_A", 4, 3, ZoneType.PRIORITY, max_drones=2)
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    category: ZoneCategory = ZoneCategory.HUB
    max_drones: int = 1
    color: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Valider les données de la zone.

        Raises:
            ValueError: Si le nom est vide ou contient des caractères invalides.
            ValueError: Si max_drones est inférieur à 1.

        Note:
            Les zones bloquées sont valides dans le graphe. Le pathfinding
            est responsable de ne jamais les utiliser.
        """
        if not self.name:
            raise ValueError("Le nom de la zone ne peut pas être vide")
        if "-" in self.name or " " in self.name:
            raise ValueError(f"Nom de zone invalide : {self.name}")
        if self.max_drones < 1:
            raise ValueError("max_drones doit être un entier positif")

    @property
    def is_start(self) -> bool:
        """Retourne True si cette zone est le hub de départ."""
        return self.category == ZoneCategory.START_HUB

    @property
    def is_end(self) -> bool:
        """Retourne True si cette zone est le hub d'arrivée."""
        return self.category == ZoneCategory.END_HUB

    @property
    def is_hub(self) -> bool:
        """Retourne True si cette zone est un hub de départ ou d'arrivée."""
        return self.is_start or self.is_end

    @property
    def is_blocked(self) -> bool:
        """Retourne True si cette zone est inaccessible."""
        return self.zone_type == ZoneType.BLOCKED

    @property
    def movement_cost(self) -> int:
        """Retourne le nombre de tours nécessaires pour entrer dans cette zone.

        Returns:
            1 pour NORMAL et PRIORITY, 2 pour RESTRICTED, 0 pour BLOCKED.

        Note:
            BLOCKED retourne 0 car le pathfinding ne doit jamais utiliser
            ces zones ; cette valeur sert de marqueur d'inaccessibilité.
        """
        match self.zone_type:
            case ZoneType.NORMAL | ZoneType.PRIORITY:
                return 1
            case ZoneType.RESTRICTED:
                return 2
            case ZoneType.BLOCKED:
                return 0
            case _:
                raise ValueError(f"Type de zone inconnu : {self.zone_type}")

    def has_capacity(self, current_occupancy: int) -> bool:
        """Retourne True si un drone supplémentaire peut occuper cette zone.

        Les zones start et end ont une capacité illimitée (exception du sujet).
        Les autres zones respectent max_drones.

        Args:
            current_occupancy: Nombre de drones actuellement dans la zone.

        Returns:
            True si la zone peut accueillir un drone de plus.

        Raises:
            ValueError: Si current_occupancy est négatif.
        """
        if current_occupancy < 0:
            raise ValueError("current_occupancy ne peut pas être négatif")
        if self.is_start or self.is_end:
            return True
        return current_occupancy < self.max_drones

    def position(self) -> tuple[int, int]:
        """Retourne les coordonnées (x, y) de la zone."""
        return (self.x, self.y)

    def __str__(self) -> str:
        """Retourne une représentation lisible de la zone."""
        return (
            f"Zone(name={self.name}, pos=({self.x}, {self.y}), "
            f"type={self.zone_type.value}, capacity={self.max_drones})"
        )

    def __repr__(self) -> str:
        """Retourne une représentation détaillée de la zone pour le débogage."""
        return (
            f"Zone(name={self.name!r}, x={self.x}, y={self.y}, "
            f"zone_type={self.zone_type!r}, category={self.category!r}, "
            f"max_drones={self.max_drones}, color={self.color!r})"
        )
