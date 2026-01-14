const vscode = require('vscode');

class ImageSidebarProvider {
  constructor(context) {
    this.context = context;
    this._view = null;
    this._disposables = [];
  }

  resolveWebviewView(webviewView) {
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.context.extensionUri]
    };

    this._update();

    this._disposables.push(vscode.window.onDidChangeActiveTextEditor(() => this._update()));
    this._disposables.push(vscode.workspace.onDidChangeTextDocument(() => this._update()));

    webviewView.onDidDispose(() => {
      this._disposables.forEach(d => d.dispose());
      this._disposables = [];
    });
  }

  _toWorkspaceUri(possiblePath, doc) {
    if (!possiblePath) return null;
    if (/^(https?:)?\/\//.test(possiblePath)) return vscode.Uri.parse(possiblePath);

    // Resolve relative to the document first, then workspace root
    try {
      if (!/^[A-Za-z]:\\/.test(possiblePath) && !possiblePath.startsWith('/')) {
        const base = vscode.Uri.file(doc.uri.fsPath).with({ path: doc.uri.fsPath });
        const resolved = vscode.Uri.joinPath(vscode.Uri.file(require('path').dirname(doc.uri.fsPath)), possiblePath);
        return resolved;
      }
      return vscode.Uri.file(possiblePath);
    } catch (e) {
      return null;
    }
  }

  _toWebviewSrc(uri, webview) {
    if (!uri) return null;
    if (uri.scheme === 'http' || uri.scheme === 'https') return uri.toString();
    return webview.asWebviewUri(uri).toString();
  }

  _extractImagePaths(text) {
    const paths = [];
    const mdRegex = /!\[[^\]]*\]\(([^)]+)\)/g;
    const htmlRegex = /<img[^>]+src=["']([^"']+)["']/g;
    let m;
    while ((m = mdRegex.exec(text))) paths.push(m[1].trim());
    while ((m = htmlRegex.exec(text))) paths.push(m[1].trim());
    return Array.from(new Set(paths));
  }

  _update() {
    if (!this._view) return;
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      this._view.webview.html = `<div style="padding:10px;color:#888">No active editor</div>`;
      return;
    }

    const doc = editor.document;
    const text = doc.getText();
    const imagePaths = this._extractImagePaths(text);

    const imagesHtml = imagePaths.map(p => {
      const uri = this._toWorkspaceUri(p, doc);
      const src = this._toWebviewSrc(uri || vscode.Uri.parse(p), this._view.webview);
      if (!src) return '';
      return `<div style="margin:6px 0"><img src="${src}" style="max-width:100%;height:auto;border:1px solid #ddd;border-radius:4px"/></div>`;
    }).join('');

    const content = imagesHtml || '<div style="padding:10px;color:#888">No images found in the active file</div>';

    this._view.webview.html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="padding:8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;">${content}</body></html>`;
  }
}

function activate(context) {
  const provider = new ImageSidebarProvider(context);
  context.subscriptions.push(vscode.window.registerWebviewViewProvider('imageSidebarView', provider));
}

function deactivate() {}

module.exports = { activate, deactivate };
