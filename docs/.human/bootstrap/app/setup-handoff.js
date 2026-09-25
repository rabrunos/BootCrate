/* Pure handoff helpers shared by the offline Setup and deterministic tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BootCrateHandoff = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const BOOTSTRAP_SOURCE = Object.freeze({
    product: "BootCrate",
    version: "0.9",
    repository: "https://github.com/rabrunos/BootCrate",
    entrypoint: "docs/.human/bootstrap/START_HERE.md"
  });
  function slugify(value) {
    return String(value || "").trim().toLowerCase().replace(/[^a-z0-9._-]+/g, "-").replace(/^[._-]+|[._-]+$/g, "").slice(0, 100);
  }
  function parseRepository(value) {
    const raw = String(value || "").trim();
    const short = raw.match(/^([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/);
    const valid = (owner, repo) => /^[A-Za-z0-9][A-Za-z0-9-]{0,38}$/.test(owner) &&
      /^[A-Za-z0-9._-]{1,100}$/.test(repo) && ![".",".."].includes(repo) && !repo.endsWith(".git.git");
    if (short) {
      const repo = short[2].replace(/\.git$/, "");
      return valid(short[1],repo) ? short[1] + "/" + repo : "";
    }
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
  function projectInstructions(repository, repositoryState = "unknown", executionProfile = "protected_manual") {
    const repo = parseRepository(repository);
    if (!repo) return "";
    if (!["protected_manual","protected_auto","full_access"].includes(executionProfile)) executionProfile = "protected_manual";
    const guide = repositoryState === "empty" || repositoryState === "none"
      ? "The target repository is empty or not yet created; materialize the approved BootCrate selection before expecting PROJECT_GUIDE.md."
      : "Read PROJECT_GUIDE.md as the stable target-project entry point when present; if it is absent, stop and determine whether materialization is still pending.";
    return [
      "Repository: " + repo + ".",
      "Bootstrap source: BootCrate v" + BOOTSTRAP_SOURCE.version + " from " + BOOTSTRAP_SOURCE.repository + "; template entry point " + BOOTSTRAP_SOURCE.entrypoint + ".",
      "For project-specific work, inspect the current repository first.",
      guide,
      "Execution permissions requested by the intake: " + executionProfile + ". Effective permissions: not observed; verify the executor and surface before acting.",
      "Technical permissions do not authorize push, publication, production changes, purchases, or secret access.",
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
  return {BOOTSTRAP_SOURCE,slugify,parseRepository,githubCreateUrl,projectInstructions,initialMessage};
});
