<template>
  <span class="bs-help">
    <svg
      width="14"
      height="13"
      viewBox="0 0 14 13"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill-rule="evenodd"
        clip-rule="evenodd"
        d="M6.51168 13C10.108 13 13.0234 10.0899 13.0234 6.5C13.0234 2.91015 10.108 0 6.51168 0C2.91538 0 0 2.91015 0 6.5C0 10.0899 2.91538 13 6.51168 13ZM7.32564 3.74653V2.7309C7.32564 2.61664 7.23661 2.52778 7.12215 2.52778H5.90121C5.78675 2.52778 5.69772 2.61664 5.69772 2.7309V3.74653C5.69772 3.86079 5.78675 3.94965 5.90121 3.94965H7.12215C7.23661 3.94965 7.32564 3.86079 7.32564 3.74653ZM8.1396 9.43403V8.4184C8.1396 8.30414 8.05057 8.21528 7.93611 8.21528H7.32564V4.96528C7.32564 4.85102 7.23661 4.76215 7.12215 4.76215H5.08725C4.97279 4.76215 4.88376 4.85102 4.88376 4.96528V5.9809C4.88376 6.09516 4.97279 6.18403 5.08725 6.18403H5.69772V8.21528H5.08725C4.97279 8.21528 4.88376 8.30414 4.88376 8.4184V9.43403C4.88376 9.54829 4.97279 9.63715 5.08725 9.63715H7.93611C8.05057 9.63715 8.1396 9.54829 8.1396 9.43403Z"
        fill="#999999"
      />
    </svg>

    <q-tooltip v-bind="{ ...tooltipProps, ...$attrs }">
      <slot v-if="$slots.default"></slot>
      <span v-else>{{ text || "info message" }}</span>
    </q-tooltip>
  </span>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import type { PropType } from "vue";
import { QTooltip } from "quasar";

enum TooltipSide {
  top = "top",
  bottom = "bottom",
  left = "left",
  right = "right",
}

export default defineComponent({
  name: "default",
  components: {
    QTooltip,
  },
  props: {
    text: String,
    side: {
      type: String as PropType<"bottom" | "left" | "right" | "top">,
      default: "bottom",
    },
  },
  data() {
    return {
      showing: false,
    };
  },
  computed: {
    tooltipProps(): Record<string, any> {
      if (this.side === TooltipSide.bottom) {
        return {
          offset: [0, 5],
        };
      } else if (this.side === TooltipSide.top) {
        return {
          offset: [0, 5],
          anchor: "top middle",
          self: "bottom middle",
          "transition-show": "jump-up",
          "transition-hide": "jump-down",
        };
      } else if (this.side === TooltipSide.left) {
        return {
          offset: [5, 0],
          anchor: "center left",
          self: "center right",
          "transition-show": "jump-left",
          "transition-hide": "jump-right",
        };
      } else if (this.side === TooltipSide.right) {
        return {
          offset: [5, 0],
          anchor: "center right",
          self: "center left",
          "transition-show": "jump-right",
          "transition-hide": "jump-left",
        };
      }
      return {};
    },
  },
});
</script>

<style scoped lang="scss">
.bs-help {
  width: 1rem;
  height: 1rem;
  display: inline-block;

  color: #333;

  svg {
    color: inherit;
    fill: currentColor;
  }
}
</style>
