#!/usr/bin/env python
"""
Interactive project initialization script.

Guides the user through initial setup:
1. Check environment
2. Configure .env file
3. Generate embeddings
4. Verify setup
"""
import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")


def print_step(step_num, total_steps, text):
    """Print a step indicator."""
    print(f"\n[Step {step_num}/{total_steps}] {text}")
    print("-" * 60)


def check_venv():
    """Check if running in a virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    return in_venv


def setup_env_file():
    """Guide user through .env file setup."""
    env_path = Path(".env")
    example_path = Path(".env.example")

    if env_path.exists():
        print("✓ .env file already exists")
        overwrite = input("Do you want to reconfigure it? (y/N): ").lower()
        if overwrite != 'y':
            return True

    if not example_path.exists():
        print("✗ .env.example not found!")
        return False

    # Copy example file
    with open(example_path, 'r') as f:
        example_content = f.read()

    print("\nConfiguring .env file...")
    print("Please provide the following information:\n")

    # Ask for API key
    api_key = input("Enter your OpenAI API key (starts with 'sk-'): ").strip()
    if not api_key.startswith('sk-'):
        print("⚠ Warning: API key should start with 'sk-'")

    # Ask for other settings
    use_defaults = input("\nUse default settings for other values? (Y/n): ").lower()

    if use_defaults != 'n':
        # Just replace the API key
        content = example_content.replace(
            "OPENAI_API_KEY=your-openai-api-key-here",
            f"OPENAI_API_KEY={api_key}"
        )
    else:
        # Interactive configuration
        debug = input("Enable debug mode? (y/N): ").lower() == 'y'
        redis_host = input("Redis host (default: localhost): ").strip() or "localhost"
        redis_port = input("Redis port (default: 6379): ").strip() or "6379"

        content = example_content.replace(
            "OPENAI_API_KEY=your-openai-api-key-here",
            f"OPENAI_API_KEY={api_key}"
        ).replace(
            "DEBUG=False",
            f"DEBUG={debug}"
        ).replace(
            "REDIS_HOST=localhost",
            f"REDIS_HOST={redis_host}"
        ).replace(
            "REDIS_PORT=6379",
            f"REDIS_PORT={redis_port}"
        )

    # Write .env file
    with open(env_path, 'w') as f:
        f.write(content)

    print("\n✓ .env file created successfully")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling dependencies from requirements.txt...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        return False


def install_spacy_model():
    """Install spaCy language model."""
    print("\nInstalling spaCy language model...")

    try:
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            check=True
        )
        print("✓ spaCy model installed")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install spaCy model")
        return False


def generate_embeddings():
    """Run embedding generation script."""
    print("\nGenerating embeddings...")
    print("This will make API calls to OpenAI (estimated cost: ~$0.01-0.02)")

    proceed = input("Proceed with embedding generation? (Y/n): ").lower()
    if proceed == 'n':
        print("⚠ Skipping embedding generation")
        print("  You'll need to run it manually later:")
        print("  python scripts/generate_embeddings.py")
        return False

    use_extended = input("Use extended anchor set? (recommended for production) (Y/n): ").lower()
    extended_flag = "" if use_extended == 'n' else "--extended"

    try:
        subprocess.run(
            [sys.executable, "scripts/generate_embeddings.py", extended_flag],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to generate embeddings")
        return False


def run_setup_check():
    """Run the setup verification script."""
    print("\nRunning setup verification...")

    try:
        subprocess.run(
            [sys.executable, "scripts/check_setup.py"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        print("✗ Setup check failed")
        return False


def main():
    """Main initialization workflow."""
    print_header("Animal Encyclopedia - Project Initialization")

    print("This script will guide you through setting up the project.")
    print("Make sure you have:")
    print("  • Python 3.8+ installed")
    print("  • An OpenAI API key")
    print("  • Internet connection")
    print()

    # Check virtual environment
    if not check_venv():
        print("⚠ WARNING: Not running in a virtual environment!")
        print()
        print("It's recommended to use a virtual environment:")
        print("  python -m venv .venv")
        print("  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
        print()
        proceed = input("Continue anyway? (y/N): ").lower()
        if proceed != 'y':
            print("Exiting. Please create a virtual environment first.")
            sys.exit(1)

    # Step 1: Install dependencies
    print_step(1, 5, "Installing Dependencies")
    if not install_dependencies():
        print("\n✗ Setup failed at dependency installation")
        sys.exit(1)

    # Step 2: Install spaCy model
    print_step(2, 5, "Installing spaCy Language Model")
    if not install_spacy_model():
        print("\n⚠ spaCy model installation failed, but continuing...")

    # Step 3: Configure .env
    print_step(3, 5, "Configuring Environment")
    if not setup_env_file():
        print("\n✗ Setup failed at .env configuration")
        sys.exit(1)

    # Step 4: Generate embeddings
    print_step(4, 5, "Generating Embeddings")
    embeddings_generated = generate_embeddings()

    # Step 5: Verify setup
    print_step(5, 5, "Verifying Setup")
    run_setup_check()

    # Final message
    print_header("Setup Complete!")

    if embeddings_generated:
        print("✓ Your Animal Encyclopedia is ready to use!")
        print()
        print("To start the application:")
        print("  python animal_encyclopedia/api/app.py")
        print()
        print("Or with uvicorn:")
        print("  uvicorn animal_encyclopedia.api.app:app --reload")
        print()
        print("API documentation will be available at:")
        print("  http://localhost:8000/docs")
    else:
        print("⚠ Setup complete, but embeddings were not generated.")
        print()
        print("Before starting the application, run:")
        print("  python scripts/generate_embeddings.py")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)