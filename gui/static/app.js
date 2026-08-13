"use strict";

const svg = document.getElementById("scene");
const stage = document.getElementById("stage");
const dropZone = document.getElementById("drop-zone");
const fileIcon = document.getElementById("file-icon");
const mouth = document.getElementById("mouth-profile");
const stomach = document.getElementById("stomach");
const head = document.getElementById("head");
const sponge = document.getElementById("sponge");
const statusEl = document.getElementById("status");
const previewCheckbox = document.getElementById("preview-mode");
const sbFontSize = document.getElementById("sb-font-size");
const sbHAlign = document.getElementById("sb-h-align");
const sbVAlign = document.getElementById("sb-v-align");

function collectOverrides() {
  const overrides = {};
  const fontSize = parseInt(sbFontSize.value, 10);
  if (fontSize) overrides.font_height_dots = fontSize;
  if (sbHAlign.value && sbHAlign.value !== "C") overrides.h_align = sbHAlign.value;
  if (sbVAlign.value && sbVAlign.value !== "C") overrides.v_align = sbVAlign.value;
  return overrides;
}

let headFacing = "profile";
let sequenceRunning = false;

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function toSvgPoint(clientX, clientY) {
  const pt = svg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const ctm = svg.getScreenCTM();
  return pt.matrixTransform(ctm.inverse());
}

function setStatus(msg, kind) {
  statusEl.textContent = msg;
  statusEl.classList.remove("error", "success");
  if (kind) statusEl.classList.add(kind);
}

function showFileIcon(point) {
  fileIcon.style.transition = "none";
  fileIcon.style.transform = `translate(${point.x}px, ${point.y}px) scale(1)`;
  fileIcon.classList.remove("eaten");
  fileIcon.classList.add("visible");
  void fileIcon.offsetWidth; // reflow so "transition: none" actually applies
  fileIcon.style.transition = "";
  requestAnimationFrame(() => {
    fileIcon.style.transform = "translate(800px, 198px) scale(0.15)";
  });
}

function hideFileIcon() {
  fileIcon.classList.add("eaten");
  setTimeout(() => {
    fileIcon.classList.remove("visible");
    fileIcon.style.transition = "none";
    fileIcon.style.transform = "translate(60px, 60px) scale(1)";
    void fileIcon.offsetWidth;
    fileIcon.style.transition = "";
  }, 350);
}

function turnHead(direction) {
  return new Promise((resolve) => {
    if (headFacing === direction) {
      resolve();
      return;
    }
    head.classList.add("turning");
    setTimeout(() => {
      head.classList.toggle("facing-front", direction === "front");
    }, 300); // swap the face at the moment the squish hides it
    head.addEventListener(
      "animationend",
      () => {
        head.classList.remove("turning");
        headFacing = direction;
        resolve();
      },
      { once: true }
    );
  });
}

function danceSponge() {
  return new Promise((resolve) => {
    sponge.classList.add("visible");
    setTimeout(() => {
      // landing flourish: one arm up in a woozy wave before the full flail
      sponge.classList.add("posing");
      setTimeout(() => {
        sponge.classList.remove("posing");
        sponge.classList.add("dancing");
        setTimeout(() => {
          sponge.classList.remove("dancing");
          sponge.classList.add("leaving");
          setTimeout(() => {
            sponge.classList.remove("visible", "leaving");
            resolve();
          }, 550);
        }, 2500);
      }, 500);
    }, 550);
  });
}

async function startFeedSequence(dropPoint, csvText, fileName) {
  setStatus(`Feeding ${fileName}…`);
  showFileIcon(dropPoint);

  if (headFacing === "front") {
    await turnHead("profile");
  }

  mouth.classList.add("chewing");
  stomach.classList.add("rumbling");

  const preview = previewCheckbox.checked;
  const overrides = collectOverrides();
  const resultPromise = fetch("/api/print", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ csv: csvText, preview, overrides }),
  })
    .then((r) => r.json().then((data) => ({ status: r.status, data })))
    .catch((err) => ({ status: 0, data: { ok: false, error: String(err) } }));

  const [, { data }] = await Promise.all([wait(900), resultPromise]);
  hideFileIcon();

  mouth.classList.remove("chewing");
  stomach.classList.remove("rumbling");

  if (!data.ok) {
    setStatus(data.error || "Something went wrong.", "error");
    sequenceRunning = false;
    return;
  }

  setStatus(
    data.preview
      ? `Preview: ${data.count} label(s) parsed. Test mode — nothing was printed.`
      : `Printed ${data.count} label(s) to ${data.printer}.`,
    "success"
  );

  await turnHead("front");
  await danceSponge();

  sequenceRunning = false;
}

function handleDrop(event) {
  if (sequenceRunning) return;

  const file = event.dataTransfer.files && event.dataTransfer.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".csv")) {
    setStatus(`"${file.name}" doesn't look like a CSV file.`, "error");
    return;
  }

  sequenceRunning = true;
  const dropPoint = toSvgPoint(event.clientX, event.clientY);

  const reader = new FileReader();
  reader.onload = () => startFeedSequence(dropPoint, reader.result, file.name);
  reader.onerror = () => {
    setStatus("Could not read that file.", "error");
    sequenceRunning = false;
  };
  reader.readAsText(file);
}

let dragCounter = 0;

window.addEventListener("dragenter", (e) => {
  e.preventDefault();
  if (!e.dataTransfer.types.includes("Files")) return;
  dragCounter++;
  stage.classList.add("armed");
});

window.addEventListener("dragover", (e) => e.preventDefault());

window.addEventListener("dragleave", () => {
  dragCounter = Math.max(0, dragCounter - 1);
  if (dragCounter === 0) {
    stage.classList.remove("armed", "drag-hover");
  }
});

window.addEventListener("drop", (e) => {
  e.preventDefault();
  dragCounter = 0;
  stage.classList.remove("armed", "drag-hover");
  handleDrop(e);
});

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  stage.classList.add("drag-hover");
});

dropZone.addEventListener("dragleave", () => {
  stage.classList.remove("drag-hover");
});
