# Crack Manager

This tool helps you test different versions of cracks/patches for your games. It automatically backs up the original files being replaced, allowing you to easily clean up the crack and revert the game back to its original state at any time.

**Download the `.zip` containing the ready-to-use `.exe` directly from the [Releases](../../releases) tab.**

## How to Apply a Crack

1. Open the "Apply Crack" tab
2. **Game Folder:** Select the main folder where your game is installed
3. **Crack Folder:** Select the folder containing the crack files

> ⚠️ **The Patch Folder MUST have the exact same internal folder structure as the Game Folder.**
> Do not just put loose files in the patch folder if they belong inside subfolders in the game. The tool copies the files exactly as they are structured.

4. Click "Apply Crack". The tool will back up the original files and copy the new ones.

## How to Revert to Original

Whenever you want to test a new crack or just clean up the current one:

1. Open the "Revert to original" tab
2. Select your game from the dropdown list
3. Click "Revert to original"

The tool will automatically delete all the crack files it copied and restore your original files to their exact places.

## Important Notes

* The tool works with multiple games at the same time. It keeps track of everything separately.
* When you apply your first crack, the tool will create a folder named `Original Files` and a file named `patch_log.json` in the same directory as this `.exe`.
* **DO NOT DELETE** the `Original Files` folder or the `patch_log.json` file! If you delete them, the tool will not be able to restore your game.
* You can find the original source code in the `CrackManagerSource` folder.