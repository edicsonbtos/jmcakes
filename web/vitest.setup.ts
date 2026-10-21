import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// jsdom no implementa showModal/close de <dialog>: lo mínimo para probar `Sheet`.
if (typeof HTMLDialogElement !== "undefined") {
  const proto = HTMLDialogElement.prototype as HTMLDialogElement & { __polyfilled?: boolean };
  if (!proto.showModal || !proto.__polyfilled) {
    proto.showModal = function showModal(this: HTMLDialogElement) {
      this.setAttribute("open", "");
    };
    proto.show = function show(this: HTMLDialogElement) {
      this.setAttribute("open", "");
    };
    proto.close = function close(this: HTMLDialogElement) {
      this.removeAttribute("open");
      this.dispatchEvent(new Event("close"));
    };
    proto.__polyfilled = true;
  }
}

afterEach(() => {
  if (typeof document !== "undefined") cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
