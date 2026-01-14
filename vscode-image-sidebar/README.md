Image Sidebar — VS Code extension (minimal)

What it does
- Adds an "Images" view in the Explorer (left) that shows images referenced in the active editor.

How to run (in VS Code)
1. Open the `vscode-image-sidebar` folder in VS Code as a workspace folder.
2. Press F5 to launch an Extension Development Host.
3. Open a file that contains image references (Markdown `![alt](path)` or HTML `<img src="...">`).
4. Open the Explorer view and expand the `Images` view — images found in the active file will be displayed.

Notes
- Relative paths are resolved relative to the active file.
- Remote (http/https) images are supported.
- This is a minimal scaffold; feel free to enhance features (filtering, caching, thumbnails, refresh command, configuration).
