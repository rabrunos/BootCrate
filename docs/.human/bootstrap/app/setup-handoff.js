/* Pure handoff helpers shared by the offline Setup and deterministic tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BootCrateHandoff = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  function slugify(value) {
    return String(value || "").trim().toLowerCase().replace(/[^a-z0-9._-]+/g, "-").replace(/^[._-]+|[._-]+$/g, "").slice(0, 100);
  }
  function parseRepository(value) {
    const raw = String(value || "").trim();
    const short = raw.match(/^([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/);
    if (short) return short[1] + "/" + short[2];
    try {
      const url = new URL(raw);
      if (url.protocol !== "https:" || url.hostname !== "github.com") return "";
      const parts = url.pathname.replace(/^\/+|\/+$/g, "").split("/");
      if (parts.length !== 2 || !parts.every(Boolean)) return "";
      return parts[0] + "/" + parts[1].replace(/\.git$/, "");
    } catch { return ""; }
  }
  function githubCreateUrl(input) {
    const url = new URL("https://github.com/new");
    url.searchParams.set("template_owner", "rabrunos");
    url.searchParams.set("template_name", "BootCrate");
    const name = slugify(input && input.name);
    if (name) url.searchParams.set("name", name);
    const description = String(input && input.description || "").trim().slice(0, 350);
    if (description) url.searchParams.set("description", description);
    if (input && ["public", "private"].includes(input.visibility)) url.searchParams.set("visibility", input.visibility);
    return url.toString();
  }
  function projectInstructions(repository) {
    const repo = parseRepository(repository);
    if (!repo) return "";
    return [
      "Repository: " + repo + ".",
      "For project-specific work, inspect the current repository first.",
      "Read PROJECT_GUIDE.md as the stable entry point for the project's current workflow and context.",
      "GitHub is the remotely observable source of truth; Issues own active work state.",
      "Implementation agents verify local execution state before changing files.",
      "Do not ask the owner to reconstruct information recoverable from the repository."
    ].join("\n");
  }
  function initialMessage(language) {
    return language === "pt-BR"
      ? "Este é o intake inicial do projeto. Leia PROJECT_GUIDE.md e inspecione o estado atual do repositório. Use minhas respostas como intenção e restrições, não como decisões técnicas finais. Pesquise fatos externos relevantes e discuta comigo decisões materiais antes da implementação. Não implemente, provisione ou publique nada antes de definirmos o escopo de materialização."
      : "This is the project's initial intake. Read PROJECT_GUIDE.md and inspect the current repository state. Treat my answers as intent and constraints, not final technical decisions. Research material external facts and discuss consequential decisions with me before implementation. Do not implement, provision, or publish anything until we agree on the materialization scope.";
  }
  return {slugify, parseRepository, githubCreateUrl, projectInstructions, initialMessage};
});
