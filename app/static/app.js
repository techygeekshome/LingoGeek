const $ = (id) => document.getElementById(id);
let PAIRS = [];

const bytes = (n) => {
  if (!n) return "";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i += 1; }
  return `${n.toFixed(n < 10 && i > 0 ? 1 : 0)} ${u[i]}`;
};

async function loadLanguages() {
  const r = await fetch("/api/languages");
  if (!r.ok) { $("note").textContent = "The language list could not be loaded."; return; }
  const data = await r.json();
  PAIRS = data.pairs;

  // This runs again every time the queue empties, to pick up a pack that was
  // just downloaded. Whatever the person had chosen must survive that, or the
  // language quietly changes under them between one batch and the next.
  const hadFrom = $("from").value;
  const hadTo = $("to").value;

  const froms = [...new Map(PAIRS.map((p) => [p.from_code, p.from_name])).entries()]
    .sort((a, b) => a[1].localeCompare(b[1]));
  $("from").innerHTML = froms.map(([c, n]) => `<option value="${c}">${n}</option>`).join("");
  if (hadFrom && froms.some(([c]) => c === hadFrom)) $("from").value = hadFrom;
  else $("from").value = froms.some(([c]) => c === "en") ? "en" : froms[0][0];

  if (data.installed_bytes) $("disk").textContent = `${bytes(data.installed_bytes)} of language packs`;
  fillTargets(hadTo);
}

function fillTargets(keep) {
  const from = $("from").value;
  const targets = PAIRS.filter((p) => p.from_code === from)
    .sort((a, b) => a.to_name.localeCompare(b.to_name));
  $("to").innerHTML = targets.map((p) => `<option value="${p.to_code}">${p.to_name}</option>`).join("");
  if (keep && targets.some((p) => p.to_code === keep)) $("to").value = keep;
  showPack();
}

function currentPair() {
  return PAIRS.find((p) => p.from_code === $("from").value && p.to_code === $("to").value);
}

function showPack() {
  const p = currentPair();
  const el = $("packstate");
  el.className = "pill";
  if (!p) { el.textContent = "not available"; return; }
  if (p.installed) { el.classList.add("have"); el.textContent = "language pack ready"; }
  else { el.classList.add("need"); el.textContent = "downloads once, then works offline"; }
}

async function send(paths) {
  const p = currentPair();
  if (!p) { $("note").textContent = "That pair of languages is not available."; return; }
  const r = await fetch("/api/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths, pair: p.key }),
  });
  const out = await r.json();
  $("note").textContent = (out.skipped || []).length
    ? out.skipped.map((s) => `${s.name}: ${s.why}`).join(" · ")
    : "";
  poll();
}

function render(items) {
  $("queuepanel").hidden = items.length === 0;
  $("queue").innerHTML = items.map((i) => {
    const pct = i.total_blocks ? Math.round((i.done_blocks / i.total_blocks) * 100) : 0;
    const label = {
      waiting: "waiting",
      downloading: i.total_blocks
        ? `downloading the language pack ${pct}%`
        : "downloading the language pack",
      // total_blocks is 0 until the handler has counted the file, which is a
      // moment or two on a large document. "0 of 0" reads like a fault.
      working: i.total_blocks
        ? `translating ${i.done_blocks} of ${i.total_blocks}`
        : "translating",
      done: i.message || "done",
      failed: i.message || "failed",
    }[i.state] || i.state;
    return `<li>
      <div class="qhead"><span class="qname">${i.name}</span>
        <span class="state ${i.state}">${label}</span></div>
      ${i.state === "done" || i.state === "failed" ? "" :
        `<div class="track"><div class="fill" style="width:${pct}%"></div></div>`}
      ${i.output ? `<div class="out">Written to ${i.output}</div>` : ""}
      ${(i.warnings || []).map((w) => `<div class="warn">${w}</div>`).join("")}
    </li>`;
  }).join("");
}

let timer = null;
async function poll() {
  const r = await fetch("/api/queue");
  const { items } = await r.json();
  render(items);
  const busy = items.some((i) => i.state === "waiting" || i.state === "working" || i.state === "downloading");
  clearTimeout(timer);
  if (busy) timer = setTimeout(poll, 600);
  else loadLanguages();
}

const drop = $("drop"), picker = $("picker");
drop.addEventListener("click", () => picker.click());
picker.addEventListener("change", () => {
  const paths = [...picker.files].map((f) => f.path).filter(Boolean);
  if (paths.length) send(paths);
  picker.value = "";
});
["dragenter", "dragover"].forEach((e) =>
  drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((e) =>
  drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (ev) => {
  const paths = [...ev.dataTransfer.files].map((f) => f.path).filter(Boolean);
  if (paths.length) send(paths);
});

$("from").addEventListener("change", () => fillTargets());
$("to").addEventListener("change", showPack);

loadLanguages();
poll();
