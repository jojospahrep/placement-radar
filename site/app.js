(() => {
  const cfg = window.RADAR_CONFIG || {};
  const $ = (id) => document.getElementById(id);
  const PAGE = 40;
  const DAY = 86400000;
  const today = new Date(new Date().toDateString());
  const REGIONS = {
    london: /london|brentford|uxbridge|heathrow|slough/i,
    south: /reading|bracknell|wokingham|guildford|woking|weybridge|farnborough|basingstoke|southampton|portsmouth|oxford|abingdon|didcot|culham|harwell|bicester|milton park|grove|banbury|brackley|silverstone|stevenage|hatfield|harlow|welwyn|watford|hemel|high wycombe|luton|milton keynes|cambridge|huntingdon|peterborough|chelmsford|colchester|basildon|ipswich|norwich|crawley|brighton|rochester|maidstone/i,
    midlands: /birmingham|coventry|solihull|gaydon|wellesbourne|derby|nottingham|leicester|loughborough|lutterworth|stafford|stoke|wolverhampton|telford|shrewsbury|burton|worcester|lincoln/i,
    north: /manchester|liverpool|leeds|sheffield|newcastle|sunderland|durham|middlesbrough|teesside|york|hull|brough|preston|warton|barrow|warrington|chester|crewe|macclesfield|stockport|bolton|runcorn|ellesmere/i,
    scotland: /scotland|edinburgh|glasgow|aberdeen|dundee|inverness/i,
    wales: /wales|cardiff|swansea|newport|bridgend|wrexham|bristol|filton|bath|gloucester|cheltenham|swindon|chippenham|malmesbury|stonehouse|wotton|exeter|plymouth|poole|bournemouth/i,
  };
  const state = { q: "", type: "", disc: "", sector: "", region: "", sort: "deadline", newOnly: false, shown: PAGE };
  let jobs = [];

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const days = (iso) => Math.round((new Date(iso) - today) / DAY);
  const fmt = (iso) => new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  const isNew = (j) => (today - new Date(j.first_seen)) / DAY <= 7;
  const TYPE = { placement: "Year placement", internship: "Summer internship", insight: "Insight / spring week" };

  function matches(j) {
    if (state.type && j.type !== state.type) return false;
    if (state.disc && !j.disciplines.includes(state.disc)) return false;
    if (state.sector && j.sector !== state.sector) return false;
    if (state.newOnly && !isNew(j)) return false;
    const where = j.location + " " + j.also_at.join(" ");
    if (state.region && !REGIONS[state.region].test(where)) return false;
    if (state.q) {
      const hay = `${j.title} ${j.company} ${where} ${j.disciplines.join(" ")} ${j.snippet}`.toLowerCase();
      if (!state.q.split(/\s+/).every((w) => hay.includes(w))) return false;
    }
    return true;
  }

  function sorted(list) {
    const by = {
      deadline: (a, b) => (a.deadline || "9999").localeCompare(b.deadline || "9999") || b.first_seen.localeCompare(a.first_seen),
      new: (a, b) => b.first_seen.localeCompare(a.first_seen) || a.company.localeCompare(b.company),
      company: (a, b) => a.company.localeCompare(b.company) || a.title.localeCompare(b.title),
    }[state.sort];
    return list.slice().sort(by);
  }

  function card(j) {
    const d = j.deadline ? days(j.deadline) : null;
    const soon = d !== null && d <= 14;
    const deadline = j.deadline
      ? `<div class="deadline${soon ? " soon" : ""}">Closes <b>${fmt(j.deadline)}</b>${d <= 0 ? "today" : d === 1 ? "tomorrow" : `in ${d} days`}</div>`
      : `<div class="deadline">No closing date<b>Apply early</b></div>`;
    const where = j.location.split(";")[0] + (j.also_at.length ? ` +${j.also_at.length} more` : "");
    return `<li class="job">
      <div><h2><a href="${esc(j.url)}" target="_blank" rel="noopener">${esc(j.title)}</a></h2>
      <div class="co">${esc(j.company)} · ${esc(where)}</div></div>
      ${deadline}
      <div class="meta">
        ${isNew(j) ? '<span class="tag new">New</span>' : ""}
        <span class="tag ${j.type}">${TYPE[j.type]}</span>
        ${j.cycle ? `<span class="tag">${esc(j.cycle)}</span>` : ""}
        ${j.disciplines.map((t) => `<span class="tag">${esc(t)}</span>`).join("")}
      </div></li>`;
  }

  function render() {
    const list = sorted(jobs.filter(matches));
    $("jobs").innerHTML = list.slice(0, state.shown).map(card).join("");
    $("count").textContent = `${list.length} role${list.length === 1 ? "" : "s"}`;
    $("more").hidden = list.length <= state.shown;
    $("empty").hidden = list.length > 0;
  }

  function fillSelect(id, values) {
    const sel = $(id);
    for (const v of values) sel.insertAdjacentHTML("beforeend", `<option>${esc(v)}</option>`);
  }

  function bind() {
    const reset = () => { state.shown = PAGE; render(); };
    $("q").addEventListener("input", (e) => { state.q = e.target.value.trim().toLowerCase(); reset(); });
    for (const k of ["disc", "sector", "region", "sort"]) $(k).addEventListener("change", (e) => { state[k] = e.target.value; reset(); });
    $("newonly").addEventListener("change", (e) => { state.newOnly = e.target.checked; reset(); });
    $("types").addEventListener("click", (e) => {
      const b = e.target.closest("button"); if (!b) return;
      for (const x of $("types").children) x.classList.toggle("on", x === b);
      state.type = b.dataset.type; reset();
    });
    $("more").addEventListener("click", () => { state.shown += PAGE; render(); });
    $("signup").addEventListener("submit", subscribe);
    if (cfg.contactEmail) $("contact").href = `mailto:${cfg.contactEmail}?subject=Featured%20listing`;
  }

  async function subscribe(e) {
    e.preventDefault();
    const email = $("email").value.trim();
    const msg = $("signup-msg");
    if (!cfg.buttondownUser) {
      try { localStorage.setItem("radar-email", email); } catch {}
      msg.textContent = "Thanks! The mailing list opens very soon. We've noted your interest on this device.";
      return;
    }
    try {
      const body = new URLSearchParams({ email, tag: "website" });
      await fetch(`https://buttondown.com/api/emails/embed-subscribe/${encodeURIComponent(cfg.buttondownUser)}`, { method: "POST", body, mode: "no-cors" });
      msg.textContent = "Nearly there: check your inbox to confirm your subscription.";
      $("email").value = "";
    } catch {
      msg.textContent = "Couldn't reach the mailing list. Please try again in a minute.";
    }
  }

  async function load() {
    bind();
    try {
      const [j, m] = await Promise.all([fetch("data/jobs.json").then((r) => r.json()), fetch("data/meta.json").then((r) => r.json())]);
      jobs = j;
      $("m-open").textContent = m.open;
      $("m-place").textContent = m.by_type.placement;
      $("m-intern").textContent = m.by_type.internship;
      $("m-soon").textContent = jobs.filter((x) => x.deadline && days(x.deadline) <= 14).length;
      $("m-tracked").textContent = m.employers_tracked;
      $("m-updated").textContent = new Date(m.updated_at).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
      fillSelect("disc", [...new Set(jobs.flatMap((x) => x.disciplines))].sort());
      fillSelect("sector", [...new Set(jobs.map((x) => x.sector))].sort());
      render();
    } catch (err) {
      $("count").textContent = "Couldn't load roles right now. Please refresh in a moment.";
      console.error(err);
    }
  }
  load();
})();
