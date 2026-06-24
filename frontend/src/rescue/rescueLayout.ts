import { useEffect, useState } from 'react';

/** RS-P3M responsive layout profiles for Rescue UI. */

export type RescueLayoutProfile = {
  shellMax: number;
  tileCols: number;
};

export function rescueLayoutProfile(viewportWidth: number): RescueLayoutProfile {
  if (viewportWidth < 800) {
    return { shellMax: Math.min(viewportWidth - 24, 760), tileCols: 1 };
  }
  if (viewportWidth < 1200) {
    return { shellMax: Math.min(1400, viewportWidth * 0.9), tileCols: 2 };
  }
  if (viewportWidth < 1600) {
    return { shellMax: Math.min(1400, viewportWidth * 0.9), tileCols: 2 };
  }
  return { shellMax: 1400, tileCols: 3 };
}

export function useRescueLayoutProfile(): RescueLayoutProfile {
  const [profile, setProfile] = useState(() =>
    rescueLayoutProfile(typeof window !== 'undefined' ? window.innerWidth : 1366),
  );

  useEffect(() => {
    const onResize = () => setProfile(rescueLayoutProfile(window.innerWidth));
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return profile;
}
