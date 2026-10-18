// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: orangc

const SCREENSHOTS = [
  "anime", "manga", "character", "malstats", "malupdates", "book", "giveaways", "utilities",
  "info", "time", "channels", "roles", "ban", "kick-purge", "mute", "warn", "modlog", "modlog2",
  "reports", "starboard", "trigger", "github", "fun", "fun2", "minecraft", "salawat",
];

const grid = document.getElementById("gallery");
const dialog = document.getElementById("lightbox");
const image = document.getElementById("lightbox-img");
const caption = document.getElementById("lightbox-caption");
let current = 0;

function label(name) {
  return name.replace(/\d+$/, "").replace(/-/g, " & ");
}

function show(index) {
  current = (index + SCREENSHOTS.length) % SCREENSHOTS.length;
  const name = SCREENSHOTS[current];
  image.src = `assets/screenshots/${name}.png`;
  image.alt = label(name);
  caption.textContent = label(name);
  if (!dialog.open) dialog.showModal();
}

SCREENSHOTS.forEach((name, index) => {
  const button = document.createElement("button");
  button.className = "shot";
  button.type = "button";

  const thumb = document.createElement("img");
  thumb.src = `assets/screenshots/${name}.png`;
  thumb.alt = label(name);
  thumb.loading = "lazy";

  const text = document.createElement("span");
  text.textContent = label(name);

  button.append(thumb, text);
  button.addEventListener("click", () => show(index));
  grid.append(button);
});

document.getElementById("prev").addEventListener("click", () => show(current - 1));
document.getElementById("next").addEventListener("click", () => show(current + 1));
document.getElementById("close").addEventListener("click", () => dialog.close());

// clicking the backdrop closes the dialog
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

dialog.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") show(current - 1);
  if (event.key === "ArrowRight") show(current + 1);
});
