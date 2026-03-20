# Heading TurnInto Add-on

This Docs Add-on is the client-side companion for `feishu-docx` level-one heading sync.

## Purpose

The Python writer syncs Markdown level-one headings as Feishu `ordered` blocks and prefixes the first text run with:

```text
__DOC_H1__
```

This add-on finds those tagged ordered blocks in the active document, converts them to `heading1`, and then removes the marker prefix from block text.

The current example is hard-coded to only auto-run for this synced test document:

- Wiki URL: `https://nvj4o5b5sdu.feishu.cn/wiki/G80zwLWjKi4B44ker9Vc0WB7nTX?from=from_copylink`
- Doc token: `XU6TdvUxaouAvHxx8vncrQrAnCe`

## Required Client APIs

- `DocMiniApp.getActiveDocumentRef()`
- `DocMiniApp.Selection.getSelectedBlocks()`
- `DocMiniApp.Block.turnIntoBlock()`
- `DocMiniApp.Block.getText()`
- `DocMiniApp.Block.updateTextElements()`

Official references:

- https://open.feishu.cn/document/client-docs/docs-add-on/05-api-doc/05-api-doc
- https://go.feishu.cn/s/6h7vbvKl003
- https://go.feishu.cn/s/6h7vbvKjE03

## Suggested Workflow

1. Use `feishu-docx write` to sync Markdown into the target Feishu doc.
2. Open the document in Feishu.
3. Run the add-on action.
4. The add-on checks whether the active document token is `XU6TdvUxaouAvHxx8vncrQrAnCe`.
5. If it matches, the add-on converts only ordered blocks whose text starts with `__DOC_H1__ `.
6. It prefers the current viewport first; if nothing is converted there, it traverses the document tree.

## Safety Rule

Normal ordered lists are not touched unless they contain the exact marker prefix.

## File

- [main.ts](/Users/wade/MyDocument/ScriptCode/feishu-docx/docs/addons/heading-turninto-addon/main.ts)
- [verify.mjs](/Users/wade/MyDocument/ScriptCode/feishu-docx/docs/addons/heading-turninto-addon/verify.mjs)
