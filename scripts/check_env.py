"""
Environment variables validation script.

This script validates that all required environment variables are properly configured
before the application starts. It provides clear error messages for missing variables.
"""

import os
import sys

# Define all required environment variables
REQUIRED_VARS = [
    # Add any required environment variables here
    # Example: "DISCORD_WEBHOOK_URL",
]

# Define optional but recommended environment variables
RECOMMENDED_VARS = {
    "LOG_LEVEL": "INFO",
    "VERIFY_SSL": "True",
}


def check_environment():
    """Check that all required environment variables are set."""
    missing_vars = []
    warnings = []

    # Check required variables
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing_vars.append(var)

    # Check recommended variables
    for var, default in RECOMMENDED_VARS.items():
        value = os.getenv(var)
        if not value:
            warnings.append(f"{var} (using default: {default})")

    # Print results
    if missing_vars:
        print("❌ ERREUR : Variables d'environnement manquantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("💡 Action requise :")
        print("   1. Copiez .env.example vers .env")
        print("   2. Remplissez les valeurs manquantes dans .env")
        print("   3. Relancez l'application")
        return False

    if warnings:
        print("⚠️  Variables recommandées non définies (valeurs par défaut utilisées):")
        for warning in warnings:
            print(f"   - {warning}")
        print()

    print("✅ Configuration environnement OK")
    return True


if __name__ == "__main__":
    if not check_environment():
        sys.exit(1)
    sys.exit(0)
