# macOS Share Extension

This helper provides a macOS Quick Action or Shortcuts workflow that routes Finder selections, share-sheet URLs, or shared text into the existing `notion-note-creator` CLI via `scripts/macos_share_action.py`. The script chooses the correct input type (files, URLs, or piped text) and forwards the necessary flags to `python -m src.main add-note`.

## Requirements

- Python 3.10+ (use the interpreter that already works with the project)
- Dependencies installed via `pip install -r requirements.txt`
- The repository checked out locally so the script can reference `scripts/macos_share_action.py`

## Finder Quick Action for Files

1. Open **Automator** and create a new **Quick Action**.
2. Set **Workflow receives current** to **files or folders** in **Finder**.
3. Add **Run Shell Script** and choose **/bin/zsh** (or your preferred shell).
4. Set **Pass input** to **as arguments**.
5. Paste the following shell snippet (update the path to match your clone):

   ```zsh
   /usr/bin/env python3 /Users/<you>/.../scripts/macos_share_action.py \
     --database research
   ```

6. Save the Quick Action with a descriptive name (e.g., “Save to Notion Note Creator”).
7. When you right-click a file in Finder and select the new quick action, the helper sends each selected file with `--file` to the CLI.

## Quick Action for URLs (Safari or Other Apps)

1. Create another Automator Quick Action or duplicate the previous one.
2. Set **Workflow receives current** to **URLs** in **any application**.
3. Keep **Pass input: as arguments**.
4. Use a shell snippet such as:

   ```zsh
   /usr/bin/env python3 /Users/<you>/.../scripts/macos_share_action.py
   ```

   The helper adds `--url` for the shared link, so no extra flags are required unless you want to set `--title` or `--database`.

## Share Text / Clipboard via Shortcuts

1. Open the **Shortcuts** app and build a shortcut that takes **Text** or **Clipboard** as input.
2. Add **Run Shell Script**, choose **/bin/zsh**, and set **Input** to **as arguments** or **to stdin** depending on how you want to send it:
   - **As arguments**: Shortcuts passes the text via `$1` and the helper can be run with `--text "$1"`.
   - **To stdin**: Allow the helper to read text from standard input; no `--text` flag is needed.
3. Example shell script (text via stdin):

   ```zsh
   /usr/bin/env python3 /Users/<you>/.../scripts/macos_share_action.py \
     --database research \
     --title "Shortcut Note"
   ```

   Shortcuts passes the shared text into the helper’s stdin, which the script automatically uses when no `--text` flag is provided.

## Tips

- You can combine text, URLs, and files in separate workflows but never send multiple input types simultaneously; the helper enforces the same constraint as the CLI.
- Use `--title`, `--database`, or `--tags` flags when you want the Quick Action to preconfigure metadata.
- Share the Quick Action with other machines by exporting the `.workflow` and updating the script path if necessary.

