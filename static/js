const TagStreamClient = (() => {
  let latestTs = null;
  let timer = null;

  async function tick(onTags) {
    try {
      const url = latestTs ? `/api/tags?since=${encodeURIComponent(latestTs)}` : `/api/tags`;
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      if (data && data.items && data.items.length) {
        latestTs = data.latest_ts || latestTs;
        onTags && onTags(data.items);
      }
    } catch (e) {}
  }

  function start(opts = {}) {
    const intervalMs = opts.intervalMs || 1500;
    const onTags = opts.onTags || ((items) => console.log("tags:", items));
    if (timer) clearInterval(timer);
    tick(onTags);
    timer = setInterval(() => tick(onTags), intervalMs);
  }

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
  }

  return { start, stop };
})();
