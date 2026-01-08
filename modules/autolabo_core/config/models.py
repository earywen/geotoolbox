"""
Pydantic models for AutoLabo multi-provider configuration.

This module defines the data structures for:
- Provider metadata (laboratory information)
- Matrix configuration (parsing, columns, regulatory headers, legends)
"""

from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field


# =============================================================================
# PROVIDER METADATA
# =============================================================================

class ProviderMeta(BaseModel):
    """
    Métadonnées globales d'un laboratoire.
    
    Attributes:
        id: Identifiant unique du laboratoire (ex: "agrolab", "eurofins")
        name: Nom complet du laboratoire
        key_type: Type de clé utilisé pour identifier les paramètres
        matrices: Liste des matrices supportées par ce laboratoire
    """
    id: str = Field(..., description="Identifiant unique du laboratoire")
    name: str = Field(..., description="Nom complet du laboratoire")
    key_type: Literal["internal_code", "cas_number"] = Field(
        ..., 
        description="Type de clé: 'internal_code' pour AGROLAB, 'cas_number' pour EUROFINS"
    )
    matrices: List[str] = Field(
        default_factory=list,
        description="Matrices supportées: ['sols', 'eaux', 'sup']"
    )


# =============================================================================
# MATRIX CONFIGURATION COMPONENTS
# =============================================================================

class ColumnMapping(BaseModel):
    """
    Mapping des colonnes dans les fichiers bruts du laboratoire.
    
    Les indices sont 0-based (première colonne = 0).
    """
    code: int = Field(..., description="Indice de la colonne contenant le code paramètre (REF file)")
    name: int = Field(..., description="Indice de la colonne contenant le nom du paramètre")
    unit: int = Field(..., description="Indice de la colonne contenant l'unité")
    family: Optional[int] = Field(
        default=None, 
        description="Indice de la colonne contenant la famille/groupe"
    )
    raw_code_col: Optional[int] = Field(
        default=None,
        description="Indice de la colonne code dans le fichier RAW (si différent du code REF)"
    )


class ParsingConfig(BaseModel):
    """
    Configuration du parsing des fichiers bruts laboratoire.
    """
    date_row: int = Field(..., description="Ligne contenant les dates de prélèvement")
    name_row: int = Field(..., description="Ligne contenant les noms d'échantillons")
    data_start_row: int = Field(..., description="Première ligne de données")
    date_format: str = Field(
        default="%Y%m%d", 
        description="Format des dates dans le fichier"
    )
    sample_exclude_keywords: List[str] = Field(
        default_factory=lambda: ["nan", "résultat", "resultat", "lithologie", "paramètre", "unité"],
        description="Mots-clés à exclure lors de la détection des échantillons"
    )


class RegulatoryHeader(BaseModel):
    """
    Définition d'une colonne de seuil réglementaire.
    """
    title: str = Field(..., description="Titre de l'en-tête")
    color: str = Field(..., description="Couleur de l'en-tête (green, orange, white, pink, cyan, yellow, red)")
    column: int = Field(..., description="Indice de la colonne source dans le fichier de référence")


class VirtualRowConfig(BaseModel):
    """
    Configuration d'une ligne virtuelle (somme de paramètres).
    
    Utilisé pour les sommes comme "Somme 7 PCB" ou "HAP (EPA) - somme".
    """
    key: str = Field(..., description="Clé unique de la ligne virtuelle")
    name: str = Field(..., description="Nom affiché dans le rapport")
    unit: str = Field(..., description="Unité de la somme")
    components: List[str] = Field(
        ..., 
        description="Liste des clés des paramètres composants"
    )
    ref_limits: Dict[str, str] = Field(
        default_factory=dict,
        description="Seuils réglementaires {indice_colonne: valeur}"
    )
    insert_after: Optional[str] = Field(
        default=None,
        description="Clé du paramètre après lequel insérer cette ligne"
    )


class LegendItem(BaseModel):
    """
    Un élément de la légende du tableau Excel.
    """
    bg_color: str = Field(..., description="Couleur de fond (hex: #RRGGBB)")
    font_color: str = Field(default="black", description="Couleur du texte")
    description: str = Field(..., description="Texte explicatif de la légende")


class LegendConfig(BaseModel):
    """
    Configuration complète de la légende, spécifique à chaque matrice.
    """
    notes: List[str] = Field(
        default_factory=list,
        description="Notes de bas de page (LQ, sources réglementaires, etc.)"
    )
    color_items: List[LegendItem] = Field(
        default_factory=list,
        description="Éléments colorés de la légende"
    )


# =============================================================================
# MAIN MATRIX CONFIGURATION
# =============================================================================

class MatrixConfig(BaseModel):
    """
    Configuration complète pour une matrice d'un laboratoire.
    
    Chaque matrice (sols, eaux souterraines, etc.) a sa propre configuration
    définissant le parsing, les colonnes, les seuils réglementaires et la légende.
    """
    matrix: str = Field(..., description="Identifiant de la matrice: 'sols', 'eaux', 'sup'")
    
    # Parsing
    parsing: ParsingConfig = Field(..., description="Configuration du parsing")
    
    # Columns
    columns: ColumnMapping = Field(..., description="Mapping des colonnes")
    
    # Regulatory
    regulatory_headers: List[RegulatoryHeader] = Field(
        default_factory=list,
        description="En-têtes des colonnes réglementaires"
    )
    regulatory_cols: List[int] = Field(
        default_factory=list,
        description="Indices des colonnes réglementaires dans le fichier de référence"
    )
    
    # Key mappings
    key_aliases: Dict[str, str] = Field(
        default_factory=dict,
        description="Alias de clés: {clé_brute: clé_référence}"
    )
    
    # Virtual rows (sums)
    virtual_rows: List[VirtualRowConfig] = Field(
        default_factory=list,
        description="Lignes virtuelles (sommes de paramètres)"
    )
    
    # Formatting
    formatting_mode: Literal["eaux", "sols"] = Field(
        default="eaux",
        description="Mode de formatage conditionnel"
    )
    
    # Legend
    legend: LegendConfig = Field(
        default_factory=LegendConfig,
        description="Configuration de la légende"
    )
