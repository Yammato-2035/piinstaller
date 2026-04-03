import type { PandaType } from "./pandaTypes";
import { mascotPublicUrl } from "../../lib/mascotPublicUrl";

/**
 * Panda-Motive als PNG (statt SVG), damit WebKit/Tauri die verschachtelten Sub-Ressourcen zuverlässig rendert.
 */
export const COMPANION_IMAGE_URL: Record<PandaType, string> = {
  start: mascotPublicUrl("assets/mascot/companions/start.png"),
  backup: mascotPublicUrl("assets/mascot/panda_backup.png"),
  network: mascotPublicUrl("assets/mascot/companions/network.png"),
  security: mascotPublicUrl("assets/mascot/panda_security.png"),
  docker: mascotPublicUrl("assets/mascot/companions/docker.png"),
  install: mascotPublicUrl("assets/mascot/companions/install.png"),
  debug: mascotPublicUrl("assets/mascot/panda_diagnostics.png"),
  cloud: mascotPublicUrl("assets/mascot/companions/cloud.png"),
  tutorial: mascotPublicUrl("assets/mascot/companions/tutorial.png"),
  warning: mascotPublicUrl("assets/mascot/companions/warning.png"),
  neutral: mascotPublicUrl("assets/mascot/companions/neutral.png"),
};

export const COMPANION_NEUTRAL_URL = COMPANION_IMAGE_URL.neutral;
