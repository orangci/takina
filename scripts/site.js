// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: orangc

// fade sections in as they scroll into view
const revealables = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add("in");
        observer.unobserve(entry.target);
      }
    },
    { threshold: 0.1 },
  );
  revealables.forEach((el) => observer.observe(el));
} else {
  revealables.forEach((el) => el.classList.add("in"));
}

// command browser
const browser = document.getElementById("commands-list");
if (browser && window.TAKINA_COMMANDS) {
  const groups = window.TAKINA_COMMANDS;
  const search = document.getElementById("search");
  const chips = document.getElementById("chips");
  const empty = document.getElementById("empty");
  const total = groups.reduce((sum, group) => sum + group.commands.length, 0);

  document.querySelectorAll("[data-command-count]").forEach((el) => {
    el.textContent = total;
  });

  let activeGroup = "all";

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function renderCommand([name, args, description, aliases = [], kind]) {
    const row = el("li", "cmd");

    const sig = el("div", "cmd-sig");
    const code = el("code", "", `${kind === "slash" ? "/" : "."}${name}`);
    sig.append(code);
    if (args) sig.append(" ", el("code", "args", args));
    if (kind) sig.append(el("span", "tag", kind === "slash" ? "slash only" : "prefix only"));

    const desc = el("div", "cmd-desc", description);
    if (aliases.length) desc.append(el("span", "cmd-meta", `aliases: ${aliases.join(", ")}`));

    row.append(sig, desc);
    return row;
  }

  function matches(command, query) {
    const [name, args, description, aliases = []] = command;
    return [name, args, description, ...aliases].join(" ").toLowerCase().includes(query);
  }

  function render() {
    const query = search.value.trim().toLowerCase();
    browser.replaceChildren();
    let shown = 0;

    for (const group of groups) {
      if (activeGroup !== "all" && group.id !== activeGroup) continue;
      const commands = group.commands.filter((c) => !query || matches(c, query));
      if (!commands.length) continue;
      shown += commands.length;

      const section = el("div", "group");
      section.id = group.id;
      section.append(el("h3", "", group.title));
      if (group.blurb) {
        const blurb = el("p");
        blurb.innerHTML = group.blurb;
        section.append(blurb);
      }

      const list = el("ul", "cmd-list");
      commands.forEach((c) => list.append(renderCommand(c)));
      section.append(list);

      // notes describe the automatic features, so skip them while searching
      if (group.notes && !query) {
        const notes = el("ul", "notes");
        group.notes.forEach((html) => {
          const item = el("li");
          item.innerHTML = html;
          notes.append(item);
        });
        section.append(notes);
      }
      browser.append(section);
    }

    empty.hidden = shown > 0;
  }

  function addChip(id, label) {
    const chip = el("button", "chip", label);
    chip.type = "button";
    chip.dataset.group = id;
    chip.setAttribute("aria-pressed", String(id === activeGroup));
    chip.addEventListener("click", () => {
      activeGroup = id;
      chips.querySelectorAll(".chip").forEach((c) => {
        c.setAttribute("aria-pressed", String(c.dataset.group === id));
      });
      render();
    });
    chips.append(chip);
  }

  addChip("all", "All");
  groups.forEach((group) => addChip(group.id, group.title));
  search.addEventListener("input", render);
  render();
}

// takina, bobbing about in the corner
function initSakanaWidget() {
  const takina = SakanaWidget.getCharacter("takina");
  takina.initialState = { ...takina.initialState, i: 0.007, d: 1, r: 0 };
  SakanaWidget.registerCharacter("takina-slow", takina);
  new SakanaWidget({ character: "takina-slow" }).mount("#sakana-widget");
}
window.initSakanaWidget = initSakanaWidget;
