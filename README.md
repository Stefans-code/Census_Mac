# Census ERP — macOS

Build macOS di **Census**, gestionale ERP (fatturazione, magazzino con barcode, scadenzario, statistiche).

A ogni push su `main` la GitHub Action compila l'app per **Apple Silicon** e **Intel** e produce `Census_macOS.dmg` (artifact *Census-macOS-Universal-DMG* nella tab Actions).

Build manuale in locale:

```bash
pip install -r requirements.txt pyinstaller
pyinstaller main.py --name Census --windowed --icon icon.icns \
  --collect-all customtkinter --add-data "icon.png:." --add-data "bg_watermark.png:."
```
