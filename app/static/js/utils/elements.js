// elements.js: reusable DOM elements and components

// dynamic progress bar (creates and removes its own DOM)
export class ProgressBar {
  /**
   * Create an instance. Call mount(parent[, position]) to insert into DOM.
   * @param {Object} opts
   * @param {string} [opts.containerClass="dynamics-progress-container"]
   * @param {string} [opts.barClass="dynamics-popup__progress-bar"]
   * @param {string} [opts.labelClass="dynamics-popup__progress-bar-label"]
   * @param {string} [opts.textClass="dynamics-popup__progress-bar-text"]
   * @param {string} [opts.initialText="Загрузка..."]
   */
  constructor(opts = {}) {
    this.opts = Object.assign({
      containerClass: "dynamics-progress-container",
      barClass: "dynamics-popup__progress-bar",
      labelClass: "dynamics-popup__progress-bar-label",
      textClass: "dynamics-popup__progress-bar-text",
      initiallyHidden: false,
      initialText: "Загрузка...",
    }, opts);

    this.container = null;
    this.bar = null;
    this.label = null;
    this.text = null;
    this._mounted = false;
  }

  // Build DOM structure
  _build() {
    const container = document.createElement("div");
    container.className = this.opts.containerClass;
    container.style.display = this.opts.initiallyHidden ? "none" : "block";

    const text = document.createElement("p");
    text.className = this.opts.textClass;
    text.textContent = this.opts.initialText;

    const bar = document.createElement("div");
    bar.className = this.opts.barClass;

    const label = document.createElement("span");
    label.className = this.opts.labelClass;
    label.style.width = "0%"; // fallback if CSS var is not used

    bar.appendChild(label);
    container.appendChild(text);
    container.appendChild(bar);

    this.container = container;
    this.bar = bar;
    this.label = label;
    this.text = text;
  }

  /** Mount into parent element */
  mount(parent, position = "beforeend") {
    if (!parent) throw new Error("ProgressBar.mount: parent is required");
    if (this._mounted) return this;
    this._build();
    parent.insertAdjacentElement(position, this.container);
    this._mounted = true;
    return this;
  }

  show()    { if (this._mounted) this.container.style.display = "block";  return this; }
  hide()    { if (this._mounted) this.container.style.display = "none";   return this; }

  /** Update progress and optional text */
  set(percent, statusText = null) {
    if (!this._mounted) return this;
    const clamped = Math.min(Math.max(Number(percent) || 0, 0), 100);
    // via CSS var (как раньше)
    this.bar.style.setProperty('--progress-width', `${clamped}%`);
    // fallback на width
    this.label.style.width = `${clamped}%`;
    this.label.textContent = `${Math.round(clamped)}%`;
    if (statusText !== null) this.text.textContent = statusText;
    return this;
  }

  destroy() {
    if (!this._mounted) return;
    this.container.remove();
    this.container = this.bar = this.label = this.text = null;
    this._mounted = false;
  }
}