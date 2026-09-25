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
    const valid = (owner, repo) => /^[A-Za-z0-9][A-Za-z0-9-]{0,38}$/.test(owner) &&
      /^[A-Za-z0-9._-]{1,100}$/.test(repo) && ![".",".."].includes(repo) && !repo.endsWith(".git.git");
    if (short) return valid(short[1],short[2]) ? short[1] + "/" + short[2] : "";
    try {
      const url = new URL(raw);
      if (url.protocol !== "https:" || url.hostname !== "github.com") return "";
      const parts = url.pathname.replace(/^\/+|\/+$/g, "").split("/");
      if (parts.length !== 2 || !parts.every(Boolean)) return "";
      const repo = parts[1].replace(/\.git$/, "");
      return valid(parts[0],repo) ? parts[0] + "/" + repo : "";
    } catch { return ""; }
  }
  function githubCreateUrl(input) {
    const url = new URL("https://github.com/new");
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
      "Read PROJECT_GUIDE.md as the stable entry point if it exists; an empty repository still needs materialization.",
      "GitHub is the remotely observable source of truth; Issues own active work state.",
      "Implementation agents verify local execution state before changing files.",
      "Do not ask the owner to reconstruct information recoverable from the repository."
    ].join("\n");
  }
  function initialMessage(language) {
    return language === "pt-BR"
      ? "Este é o intake inicial do projeto. Verifique o repositório informado e leia PROJECT_GUIDE.md se ele já existir. Se houver código de produto, prepare uma Adoption Sandbox isolada e um delta revisável antes de qualquer aplicação ao original. Use minhas respostas como intenção e restrições, não como decisões técnicas finais. Confirme Issues, permissões, decisões e escopo antes da implementação; não publique por consequência da validação."
      : "This is the initial project intake. Verify the indicated repository and read PROJECT_GUIDE.md if it exists. If it contains a product, prepare an isolated Adoption Sandbox and a reviewable delta before applying anything to the original. Treat my answers as intent and constraints, not final technical decisions. Confirm Issues, access, decisions and scope before implementation; validation does not authorize publication.";
  }
  return {slugify, parseRepository, githubCreateUrl, projectInstructions, initialMessage};
});
