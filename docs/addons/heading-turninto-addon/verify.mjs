import assert from "node:assert/strict";

import { autoConvertForTargetDocument, convertTaggedOrderedBlocksToHeading1 } from "./main.ts";

const calls = {
  turned: [],
  updated: [],
};

const blockTexts = new Map([
  ["blk-tagged", "__DOC_H1__ 一、文档说明与编写规范"],
  ["blk-ordered", "1. 普通列表项"],
  ["blk-heading", "__DOC_H1__ 不应处理，因为不是 ordered"],
]);

const DocMiniApp = {
  async getActiveDocumentRef() {
    return { id: "doc-1" };
  },
  Selection: {
    async getSelectedBlocks() {
      return [
        { ref: "blk-tagged", type: "ordered" },
        { ref: "blk-ordered", type: "ordered" },
        { ref: "blk-heading", type: "heading1" },
      ];
    },
  },
  Block: {
    async getText(blockRef) {
      return blockTexts.get(blockRef) ?? "";
    },
    async turnIntoBlock(blockRef, blockType) {
      calls.turned.push({ blockRef, blockType });
    },
    async updateTextElements(blockRef, payload) {
      calls.updated.push({ blockRef, payload });
    },
  },
};

const converted = await convertTaggedOrderedBlocksToHeading1(DocMiniApp);

assert.equal(converted, 1);
assert.deepEqual(calls.turned, [{ blockRef: "blk-tagged", blockType: "heading1" }]);
assert.equal(calls.updated.length, 1);
assert.equal(calls.updated[0].blockRef, "blk-tagged");
assert.equal(
  calls.updated[0].payload.elements[0].text_run.content,
  "一、文档说明与编写规范",
);

console.log("Add-on verification passed");

const autoCalls = {
  turned: [],
  updated: [],
};

const autoDocMiniApp = {
  async getActiveDocumentRef() {
    return { docToken: "XU6TdvUxaouAvHxx8vncrQrAnCe" };
  },
  getBlockRefById(docRef, blockId) {
    return { docRef, blockId };
  },
  Selection: {
    async getSelectedBlocks() {
      return [];
    },
  },
  Document: {
    async getRootBlock() {
      return {
        id: 1,
        type: "page",
        ref: "root",
        children: [2, 3],
        childSnapshots: [
          {
            id: 2,
            type: "ordered",
            ref: "blk-auto-tagged",
            children: [],
            childSnapshots: [],
            data: { plain_text: "__DOC_H1__ 二、自动转换标题" },
          },
          {
            id: 3,
            type: "ordered",
            ref: "blk-auto-normal",
            children: [],
            childSnapshots: [],
            data: { plain_text: "1. 普通列表项" },
          },
        ],
      };
    },
  },
  Viewport: {
    async getViewportBlocks() {
      return [];
    },
  },
  Block: {
    async getBlocks() {
      return [];
    },
    async getText() {
      return "";
    },
    async turnIntoBlock(blockRef, blockType) {
      autoCalls.turned.push({ blockRef, blockType });
    },
    async updateTextElements(blockRef, payload) {
      autoCalls.updated.push({ blockRef, payload });
    },
  },
};

const autoConverted = await autoConvertForTargetDocument(autoDocMiniApp);
assert.equal(autoConverted, 1);
assert.deepEqual(autoCalls.turned, [{ blockRef: "blk-auto-tagged", blockType: "heading1" }]);
assert.equal(autoCalls.updated[0].payload.elements[0].text_run.content, "二、自动转换标题");

const skippedConverted = await autoConvertForTargetDocument({
  ...autoDocMiniApp,
  async getActiveDocumentRef() {
    return { docToken: "another-doc-token" };
  },
});
assert.equal(skippedConverted, 0);

console.log("Auto-run verification passed");
