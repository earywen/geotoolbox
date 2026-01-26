"""
Provider Registry for AutoLabo multi-provider configuration.

Handles loading and caching of provider and matrix configurations.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import ProviderMeta, MatrixConfig

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for loading and caching laboratory provider configurations.

    Configuration files are stored in:
    - providers/{provider_id}/provider.yaml  → ProviderMeta
    - providers/{provider_id}/{matrix}.yaml  → MatrixConfig

    Usage:
        registry = ProviderRegistry()
        provider = registry.load_provider("agrolab")
        config = registry.load_matrix("agrolab", "sols")
    """

    _instance: Optional["ProviderRegistry"] = None
    _providers: Dict[str, ProviderMeta] = {}
    _matrix_configs: Dict[str, MatrixConfig] = {}  # Key: "provider_id:matrix"

    def __new__(cls) -> "ProviderRegistry":
        """Singleton pattern to ensure single registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers = {}
            cls._instance._matrix_configs = {}
        return cls._instance

    @property
    def providers_dir(self) -> Path:
        """Get the path to the providers directory."""
        return Path(__file__).parent / "providers"

    def load_provider(self, provider_id: str) -> ProviderMeta:
        """
        Load provider metadata from YAML file.

        Args:
            provider_id: Unique identifier for the provider (e.g., "agrolab")

        Returns:
            ProviderMeta: Validated provider metadata

        Raises:
            FileNotFoundError: If provider.yaml doesn't exist
            ValueError: If YAML validation fails
        """
        # Check cache
        if provider_id in self._providers:
            return self._providers[provider_id]

        # Build path
        provider_path = self.providers_dir / provider_id / "provider.yaml"

        if not provider_path.exists():
            # DEBUG PATH ISSUE
            logger.error(f"DEBUG: __file__={__file__}")
            logger.error(f"DEBUG: provider_path={provider_path}")
            logger.error(f"DEBUG: absolute={provider_path.resolve()}")
            try:
                if provider_path.parent.exists():
                    logger.error(f"DEBUG: Parent contents: {[p.name for p in provider_path.parent.iterdir()]}")
                else:
                    logger.error(f"DEBUG: Parent directory does not exist: {provider_path.parent}")
            except Exception as ex:
                logger.error(f"DEBUG: Error listing parent: {ex}")
                
            raise FileNotFoundError(
                f"Provider config not found: {provider_path}"
            )

        # Load and validate
        try:
            with open(provider_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            provider = ProviderMeta.model_validate(data)
            self._providers[provider_id] = provider
            logger.info(f"Loaded provider: {provider.name} ({provider_id})")
            return provider

        except Exception as e:
            logger.error(f"Failed to load provider '{provider_id}': {e}")
            raise ValueError(f"Invalid provider config: {e}") from e

    def load_matrix(self, provider_id: str, matrix: str) -> MatrixConfig:
        """
        Load matrix configuration from YAML file.

        Args:
            provider_id: Unique identifier for the provider
            matrix: Matrix identifier (e.g., "sols", "eaux")

        Returns:
            MatrixConfig: Validated matrix configuration

        Raises:
            FileNotFoundError: If matrix YAML doesn't exist
            ValueError: If YAML validation fails
        """
        cache_key = f"{provider_id}:{matrix}"

        # Check cache
        if cache_key in self._matrix_configs:
            return self._matrix_configs[cache_key]

        # Build path
        matrix_path = self.providers_dir / provider_id / f"{matrix}.yaml"

        if not matrix_path.exists():
            raise FileNotFoundError(
                f"Matrix config not found: {matrix_path}"
            )

        # Load and validate
        try:
            with open(matrix_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            config = MatrixConfig.model_validate(data)
            self._matrix_configs[cache_key] = config
            logger.info(f"Loaded matrix config: {provider_id}/{matrix}")
            return config

        except Exception as e:
            logger.error(f"Failed to load matrix '{provider_id}/{matrix}': {e}")
            raise ValueError(f"Invalid matrix config: {e}") from e

    def get_available_providers(self) -> List[str]:
        """
        List all available provider IDs.

        Returns:
            List of provider directory names that contain a provider.yaml file.
        """
        providers = []

        if not self.providers_dir.exists():
            logger.warning(f"Providers directory not found: {self.providers_dir}")
            return providers

        for item in self.providers_dir.iterdir():
            if item.is_dir() and (item / "provider.yaml").exists():
                providers.append(item.name)

        return sorted(providers)

    def get_available_matrices(self, provider_id: str) -> List[str]:
        """
        List all available matrices for a given provider.

        Args:
            provider_id: Unique identifier for the provider

        Returns:
            List of matrix names available for this provider.
        """
        provider_dir = self.providers_dir / provider_id

        if not provider_dir.exists():
            return []

        matrices = []
        for item in provider_dir.iterdir():
            if item.is_file() and item.suffix == ".yaml" and item.name != "provider.yaml":
                matrices.append(item.stem)

        return sorted(matrices)

    def clear_cache(self) -> None:
        """Clear all cached configurations."""
        self._providers.clear()
        self._matrix_configs.clear()
        logger.debug("Registry cache cleared")


# Convenience function for quick access
def get_registry() -> ProviderRegistry:
    """Get the singleton ProviderRegistry instance."""
    return ProviderRegistry()
