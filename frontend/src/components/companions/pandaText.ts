import type { PandaStatus } from "./pandaTypes";

export interface PandaStatusText {
  label: string;
  helper: string;
}

export const PANDA_STATUS_TEXT: Record<PandaStatus, PandaStatusText> = {
  success: {
    label: "Alles in Ordnung",
    helper: "Du kannst in diesem Bereich sicher weitermachen.",
  },
  info: {
    label: "Bereit",
    helper: "Es liegt aktuell kein kritisches Problem vor.",
  },
  warning: {
    label: "Bitte prüfen",
    helper: "Schau dir die Hinweise an, bevor du fortfährst.",
  },
  danger: {
    label: "Stopp",
    helper: "Bitte zuerst das Problem beheben, bevor du weitermachst.",
  },
};
