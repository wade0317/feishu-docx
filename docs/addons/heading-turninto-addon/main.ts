const LEVEL_ONE_MARKER = "__DOC_H1__ ";
const TARGET_DOC_TOKEN = "XU6TdvUxaouAvHxx8vncrQrAnCe";

type BlockLike = {
  ref: unknown;
  id?: number;
  type?: string;
  blockType?: string;
  children?: number[];
  childSnapshots?: BlockLike[];
  data?: {
    plain_text?: string;
  };
};

type DocMiniAppAPI = {
  getActiveDocumentRef: () => Promise<unknown>;
  getBlockRefById: (docRef: unknown, blockId: number) => unknown;
  Selection: {
    getSelectedBlocks: (docRef: unknown) => Promise<BlockLike[]>;
  };
  Document: {
    getRootBlock: (docRef: unknown) => Promise<BlockLike>;
  };
  Viewport: {
    getViewportBlocks: () => Promise<BlockLike[]>;
  };
  Block: {
    getBlocks: (blockRefs: unknown[]) => Promise<BlockLike[]>;
    getText: (blockRef: unknown) => Promise<string>;
    turnIntoBlock: (blockRef: unknown, blockType: "heading1") => Promise<void>;
    updateTextElements: (
      blockRef: unknown,
      payload: {
        elements: Array<{
          text_run: {
            content: string;
            text_element_style?: Record<string, unknown>;
          };
        }>;
      },
    ) => Promise<void>;
  };
};

type DocumentRefLike = {
  docToken?: string;
};

function isOrderedBlock(block: BlockLike): boolean {
  return block.type === "ordered" || block.blockType === "ordered";
}

function getDocToken(docRef: unknown): string | undefined {
  return (docRef as DocumentRefLike | undefined)?.docToken;
}

function stripMarker(text: string): string {
  return text.startsWith(LEVEL_ONE_MARKER) ? text.slice(LEVEL_ONE_MARKER.length) : text;
}

function blockPlainText(block: BlockLike): string {
  return block.data?.plain_text ?? "";
}

async function getProcessableBlocks(DocMiniApp: DocMiniAppAPI, docRef: unknown): Promise<BlockLike[]> {
  const selectedBlocks = await DocMiniApp.Selection.getSelectedBlocks(docRef);
  if (selectedBlocks.length > 0) {
    return selectedBlocks;
  }

  const rootBlock = await DocMiniApp.Document.getRootBlock(docRef);
  const collected = new Map<number, BlockLike>();
  const queue: BlockLike[] = [rootBlock];

  while (queue.length > 0) {
    const current = queue.shift();
    if (!current || typeof current.id !== "number") {
      continue;
    }
    if (collected.has(current.id)) {
      continue;
    }
    collected.set(current.id, current);

    const childSnapshots = current.childSnapshots ?? [];
    for (const child of childSnapshots) {
      queue.push(child);
    }

    const knownChildIds = new Set(childSnapshots.map((child) => child.id).filter((id): id is number => typeof id === "number"));
    const missingChildIds = (current.children ?? []).filter((id) => !knownChildIds.has(id));
    if (missingChildIds.length === 0) {
      continue;
    }

    const childRefs = missingChildIds.map((blockId) => DocMiniApp.getBlockRefById(docRef, blockId));
    const fetchedChildren = await DocMiniApp.Block.getBlocks(childRefs);
    for (const child of fetchedChildren) {
      queue.push(child);
    }
  }

  return [...collected.values()];
}

export async function convertTaggedOrderedBlocksToHeading1(
  DocMiniApp: DocMiniAppAPI,
  blocks?: BlockLike[],
): Promise<number> {
  const docRef = await DocMiniApp.getActiveDocumentRef();
  const blocksToProcess = blocks ?? (await getProcessableBlocks(DocMiniApp, docRef));
  let converted = 0;

  for (const block of blocksToProcess) {
    if (!isOrderedBlock(block)) {
      continue;
    }

    const text = blockPlainText(block) || (await DocMiniApp.Block.getText(block.ref));
    if (!text.startsWith(LEVEL_ONE_MARKER)) {
      continue;
    }

    await DocMiniApp.Block.turnIntoBlock(block.ref, "heading1");
    await DocMiniApp.Block.updateTextElements(block.ref, {
      elements: [
        {
          text_run: {
            content: stripMarker(text),
            text_element_style: {},
          },
        },
      ],
    });
    converted += 1;
  }

  return converted;
}

export async function autoConvertForTargetDocument(DocMiniApp: DocMiniAppAPI): Promise<number> {
  const docRef = await DocMiniApp.getActiveDocumentRef();
  if (getDocToken(docRef) !== TARGET_DOC_TOKEN) {
    return 0;
  }

  const viewportBlocks = await DocMiniApp.Viewport.getViewportBlocks();
  const convertedInViewport = await convertTaggedOrderedBlocksToHeading1(DocMiniApp, viewportBlocks);
  if (convertedInViewport > 0) {
    return convertedInViewport;
  }

  return convertTaggedOrderedBlocksToHeading1(DocMiniApp);
}

export { LEVEL_ONE_MARKER, TARGET_DOC_TOKEN };
