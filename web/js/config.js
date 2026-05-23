let _config = null;

export async function loadConfig() {
  if (_config) return _config;
  const res = await fetch("config/pipeline.json");
  if (!res.ok) throw new Error("Failed to load pipeline config");
  _config = await res.json();
  return _config;
}
