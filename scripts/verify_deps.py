#!/usr/bin/env python3
"""
Verify that all PR-chat dependencies are installed correctly.
"""

import sys
import importlib
from packaging import version


def check_package(name, import_name=None, min_version=None):
    """Check if a package is installed."""
    import_name = import_name or name
    
    try:
        module = importlib.import_module(import_name)
        installed_version = getattr(module, '__version__', 'unknown')
        
        if min_version and installed_version != 'unknown':
            if version.parse(installed_version) < version.parse(min_version):
                print(f"❌ {name}: {installed_version} (requires >= {min_version})")
                return False
        
        print(f"✓ {name}: {installed_version}")
        return True
    except ImportError:
        print(f"❌ {name}: NOT INSTALLED")
        return False


def main():
    print("🔍 Checking PR-chat Dependencies\n")
    
    packages = [
        ("Streamlit", "streamlit"),
        ("SQLite3", "sqlite3"),
        ("OpenAI Whisper", "whisper"),
        ("PyPDF2", "PyPDF2"),
        ("pydub", "pydub"),
        ("Requests", "requests"),
        ("python-dotenv", "dotenv"),
        ("FAISS", "faiss"),
        ("Sentence Transformers", "sentence_transformers"),
        ("NumPy", "numpy"),
        ("PyTorch", "torch"),
        ("tqdm", "tqdm"),
    ]
    
    results = []
    for name, import_name in packages:
        results.append(check_package(name, import_name))
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} packages installed!")
        print("\nYou're ready to go! Try:")
        print("  python scripts/setup_db.py")
        print("  python scripts/ingest.py <file.mp3 or file.pdf>")
        print("  streamlit run app/streamlit_app.py")
    else:
        print(f"❌ {total - passed} packages missing")
        print("\nFix with: pip install -r requirements.txt")
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
