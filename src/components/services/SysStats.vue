<template>
  <Generic :item="item" class="sysstats">
    <template #content>
      <p class="title is-4 sysstats-head">
        <span
          :class="['sysstats-dot', online ? 'is-on' : 'is-off']"
          aria-hidden="true"
        ></span>
        {{ item.name }}
        <span class="sysstats-state">{{ online ? "ONLINE" : "OFFLINE" }}</span>
      </p>
      <p v-if="item.subtitle" class="subtitle is-6 sysstats-sub">
        {{ item.subtitle }}
      </p>
      <div v-if="error" class="subtitle is-6 sysstats-error">{{ error }}</div>
      <div v-else class="sysstats-grid">
        <div class="sysstats-metric">
          <div class="sysstats-value">{{ cpuText }}</div>
          <div class="sysstats-label">CPU</div>
          <div class="sysstats-meter">
            <div :style="{ width: meter(cpu) }"></div>
          </div>
        </div>
        <div class="sysstats-metric">
          <div class="sysstats-value">{{ ramText }}</div>
          <div class="sysstats-label">RAM</div>
          <div class="sysstats-meter">
            <div :style="{ width: meter(ram) }"></div>
          </div>
          <div class="sysstats-detail">{{ ramDetail }}</div>
        </div>
        <div class="sysstats-metric">
          <div class="sysstats-value">{{ diskText }}</div>
          <div class="sysstats-label">Storage</div>
          <div class="sysstats-meter">
            <div :style="{ width: meter(disk) }"></div>
          </div>
          <div class="sysstats-detail">{{ diskDetail }}</div>
        </div>
        <div class="sysstats-metric">
          <div class="sysstats-value">{{ uptimeText }}</div>
          <div class="sysstats-label">Uptime</div>
          <div class="sysstats-detail">{{ footText }}</div>
        </div>
      </div>
    </template>
  </Generic>
</template>

<script>
import service from "@/mixins/service.js";

export default {
  name: "SysStats",
  mixins: [service],
  props: {
    item: Object,
  },
  data: () => ({
    cpu: null,
    ram: null,
    ramUsed: null,
    ramTotal: null,
    disk: null,
    diskUsed: null,
    diskTotal: null,
    uptimeSeconds: null,
    temperature: null,
    gpu: null,
    gpuNote: null,
    online: false,
    error: null,
  }),
  computed: {
    cpuText() {
      return this.cpu == null ? "--" : `${Math.round(this.cpu)}%`;
    },
    ramText() {
      if (this.ramUsed == null || this.ramTotal == null) return "--";
      return `${this.ramUsed.toFixed(1)} / ${this.ramTotal.toFixed(1)} GB`;
    },
    ramDetail() {
      return this.ram == null ? "--" : `${Math.round(this.ram)}% used`;
    },
    diskText() {
      if (this.diskUsed == null || this.diskTotal == null) return "--";
      return `${this.diskUsed.toFixed(0)} / ${this.diskTotal.toFixed(0)} GB`;
    },
    diskDetail() {
      return this.disk == null ? "--" : `${Math.round(this.disk)}% used`;
    },
    uptimeText() {
      if (this.uptimeSeconds == null) return "--";
      const h = Math.floor(this.uptimeSeconds / 3600);
      const m = Math.floor((this.uptimeSeconds % 3600) / 60);
      if (h > 0) return `${h}h ${m}m`;
      return `${m}m`;
    },
    footText() {
      const parts = [];
      if (this.temperature != null) parts.push(`${this.temperature}°C`);
      if (this.gpu) parts.push(this.gpu);
      else if (this.gpuNote) parts.push(this.gpuNote);
      return parts.join(" · ") || "live";
    },
  },
  created() {
    // Re-run on the global scheduler interval (updateIntervalMs).
    this.autoUpdateMethod = this.fetchStat;

    // Initial data fetch
    this.fetchStat();
  },
  methods: {
    // NOTE: this.fetch() resolves against item.url/endpoint, so the card
    // must use url: "" (same origin, served by server.py at /api/stats).
    // Native fetch is intentionally not used here so proxy headers,
    // credentials and the mock server (endpoint: <mock>/sysstats) keep
    // working through the shared mixin.
    fetchStat: async function () {
      this.fetch("api/stats")
        .then((response) => {
          this.error = null;
          this.online = true;
          this.cpu = response.cpu_percent;
          this.ram = response.ram_percent;
          this.ramUsed = response.ram_used_gb;
          this.ramTotal = response.ram_total_gb;
          this.disk = response.disk_percent;
          this.diskUsed = response.disk_used_gb;
          this.diskTotal = response.disk_total_gb;
          this.uptimeSeconds = response.uptime_seconds;
          this.temperature = response.temperature_c;
          this.gpu = response.gpu_label;
          this.gpuNote = response.gpu_mem_note;
        })
        .catch((e) => {
          console.log(e);
          this.online = false;
          // Surface the reason (bad URL vs. bad payload) so the card
          // itself tells us why the backend is unreachable.
          this.error = `Unable to get system stats (${e?.message || e})`;
        });
    },
    meter(value) {
      const pct = Math.max(0, Math.min(100, Number(value) || 0));
      return `${pct}%`;
    },
  },
};
</script>

<style scoped lang="scss">
// Homer caps every card at 85px; a 4-metric grid needs its natural height.
:deep(.card-content) {
  height: auto;
}
:deep(.media-content) {
  overflow: visible;
}

.sysstats-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sysstats-state {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.sysstats-sub {
  margin-bottom: 2px;
}

.sysstats-error {
  margin-top: 6px;
}

// Modz dashboard look: small metric blocks with a gradient headline,
// uppercase label and a thin glowing meter bar.
.sysstats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.sysstats-metric {
  min-width: 0;
}

.sysstats-value {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  background: linear-gradient(120deg, #eef2ff, #b9c9ff 70%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

// Gradient headlines are built for dark surfaces: fall back to plain
// theme text when Homer runs in light mode so numbers stay readable.
:global(#app.light) .sysstats-value {
  background: none;
  color: var(--text-title);
}

.sysstats-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  opacity: 0.65;
  margin-top: 2px;
}

.sysstats-detail {
  font-size: 0.72rem;
  opacity: 0.65;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-variant-numeric: tabular-nums;
}

.sysstats-meter {
  margin-top: 8px;
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(127, 140, 160, 0.25);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.25);
}

.sysstats-meter > div {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5b8cff, #9b6cff);
  box-shadow: 0 0 10px -2px rgba(91, 140, 255, 0.45);
  transition: width 0.7s ease;
}

// Status dot with the modz glow (ping ring only when motion is allowed).
.sysstats-dot {
  position: relative;
  width: 9px;
  height: 9px;
  flex: 0 0 9px;
  border-radius: 50%;
  display: inline-block;

  &.is-on {
    background: #3ecf8e;
    box-shadow: 0 0 8px rgba(62, 207, 142, 0.5);
  }

  &.is-off {
    background: #ef5d6a;
  }

  &.is-on::after {
    content: "";
    position: absolute;
    inset: -3px;
    border-radius: 50%;
    border: 1px solid currentColor;
    color: #3ecf8e;
    opacity: 0.6;
    animation: sysstats-ping 1.9s ease-out infinite;
  }
}

@keyframes sysstats-ping {
  from {
    transform: scale(0.7);
    opacity: 0.7;
  }
  to {
    transform: scale(2.1);
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sysstats-dot.is-on::after,
  .sysstats-meter > div {
    animation: none;
    transition: none;
  }
}
</style>

