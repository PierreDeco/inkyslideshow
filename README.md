# Inky Slideshow

Diaporama photo pour écran Pimoroni Inky Impression sur Raspberry Pi.

Affiche les images d'un dossier en rotation, avec un bouton pour passer à l'image suivante.

## Matériel requis

- Raspberry Pi (Zero, 3, 4, etc.)
- [Inky Impression](https://shop.pimoroni.com/products/inky-impression) (4", 5.65" ou 7.3")
- Carte SD avec Raspberry Pi OS

## Prérequis logiciels

```bash
sudo apt update
sudo apt install python3-pip python3-pil python3-numpy
sudo pip3 install inky gpiozero numpy opencv-python-headless
```

> **Note :** `opencv-python-headless` est optionnel. Il permet de détecter les visages pour améliorer l'orientation des images portrait. Sans lui, le programme utilise uniquement l'analyse des bords.

## Installation

1. Clonez ou copiez `inkyslideshow.py` sur le Raspberry Pi.

2. Créez le dossier pour les photos :

```bash
mkdir -p ~/inky/inky/inkyslideshow/Photos
```

3. Placez vos images dans ce dossier (`Photos/`).

## Configuration

Modifiez les variables en haut de `inkyslideshow.py` :

```python
PHOTOS_FOLDER = Path.home() / "inky" / "inky" / "inkyslideshow" / "Photos"
DELAY_SECONDS = 60          # Intervalle entre chaque image (secondes)
```

Pour utiliser un autre dossier :

```python
PHOTOS_FOLDER = Path("/chemin/vers/vos/photos")
```

## Utilisation

```bash
python3 inkyslideshow.py
```

### Contrôle

| Action | Description |
|--------|-------------|
| **Attente automatique** | L'écran change d'image toutes les `DELAY_SECONDS` secondes |
| **Bouton A** | Appuyez sur le bouton A de l'Inky Impression pour passer immédiatement à l'image suivante |

## Fonctionnement

- Le programme parcourt les images du dossier configuré dans un ordre aléatoire.
- Les images sont redimensionnées pour s'adapter à l'écran (conservation du ratio).
- Les orientations EXIF sont automatiquement corrigées.
- Pour les images portrait sans métadonnées EXIF, une détection heuristique (analyse des bords, et optionally visages) est appliquée.

## Logs

Les logs sont écrits dans :
- `~/.inky_slideshow/debug.log` — fichier
- stdout — console

```bash
tail -f ~/.inky_slideshow/debug.log
```

## Dépannage

**Aucune image affichée**
- Vérifiez que le dossier `Photos` existe et contient des images (`.png`, `.jpg`, `.jpeg`, `.bmp`).
- Vérifiez les logs : `tail ~/.inky_slideshow/debug.log`

**L'écran reste blanc**
- Assurez-vous que le branchement de l'Inky Impression est correct.
- Essayez de redémarrer : `sudo reboot`

**Erreur "No module named 'inky'"**
- Réinstallez les dépendances (voir section Prérequis logiciels).

**L'image apparaît pivotée**
- Certaines images portrait sans EXIF peuvent nécessiter une rotation manuelle.
- Pour désactiver la détection automatique, remplacez `if image.height > original.width and not seems_upright(image):` par `if False:` dans `prepare_image()`.
