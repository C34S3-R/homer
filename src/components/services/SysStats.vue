<template>
  <Generic :item="item">
    <template #content>
      <p class="title is-4">{{ item.name }}</p>
      <p class="subtitle is-6">
        <span v-if="cpu != null" title="CPU usage">
          <i class="fa-solid fa-microchip"></i> {{ cpu }}%
        </span>
        <span v-if="cpu != null && ram != null"> / </span>
        <span v-if="ram != null" :title="`RAM usage (${ramUsed} of ${ramTotal} GB)`">
          <i class="fa-solid fa-memory"></i> {{ ram }}%
        </span>
        <span v-if="disk != null"> / </span>
        <span v-if="disk != null" :title="`Storage used (${diskUsed} of ${diskTotal} GB)`">
          <i class="fa-solid fa-hard-drive"></i> {{ disk }}%
        </span>
      </p>
      <p v-if="gpu" class="subtitle is-7" :title="gpuNote">
        <i class="fa-solid fa-display"></i> {{ gpu }}
      </p>
      <p v-if="error" class="subtitle is-6">{{ error }}</p>
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
    gpu: null,
    gpuNote: null,
    error: null,
  }),
  created() {
    // TEMP DEBUG beacon (remove after diagnosing): proves created() ran.
    try {
      window.fetch("/api/health?probe=sysstats-created", { cache: "no-store" });
    } catch (e) {}
    // Set up auto-update method for the scheduler
    this.autoUpdateMethod = this.fetchStat;

    // Initial data fetch
    this.fetchStat();
  },
  methods: {
    fetchStat: async function () {
      try {
        window.fetch("/api/health?probe=sysstats-fetchstat", { cache: "no-store" });
      } catch (e) {}
      this.fetch(`/api/stats`)
        .then((response) => {
          this.error = null;
          this.cpu = response.cpu_percent;
          this.ram = response.ram_percent;
          this.ramUsed = response.ram_used_gb;
          this.ramTotal = response.ram_total_gb;
          this.disk = response.disk_percent;
          this.diskUsed = response.disk_used_gb;
          this.diskTotal = response.disk_total_gb;
          this.gpu = response.gpu_label;
          this.gpuNote = response.gpu_mem_note;
        })
        .catch((e) => {
          console.log(e);
          this.error = "Unable to get system stats";
        });
    },
  },
};
</script>
