import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { COLOR } from "../theme";

/**
 * Navy blueprint backdrop: major/minor grid, slow drift (frame-driven), centre glow
 * and vignette. Every scene and the cover sit on this so the series reads as one.
 */
export const Blueprint: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const drift = (frame * 0.4) % 120;
  return (
    <AbsoluteFill style={{ background: COLOR.bg }}>
      <AbsoluteFill
        style={{
          backgroundImage: [
            `linear-gradient(${COLOR.grid}66 2px, transparent 2px)`,
            `linear-gradient(90deg, ${COLOR.grid}66 2px, transparent 2px)`,
            `linear-gradient(${COLOR.grid}33 1px, transparent 1px)`,
            `linear-gradient(90deg, ${COLOR.grid}33 1px, transparent 1px)`,
          ].join(","),
          backgroundSize: "120px 120px, 120px 120px, 30px 30px, 30px 30px",
          backgroundPosition: `0 ${drift}px, 0 ${drift}px, 0 ${drift}px, 0 ${drift}px`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 80% 55% at 50% 52%, ${COLOR.bgRaised}AA 0%, transparent 70%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 110% 85% at 50% 45%, transparent 55%, ${COLOR.bgDeep} 100%)`,
        }}
      />
      {children}
    </AbsoluteFill>
  );
};
