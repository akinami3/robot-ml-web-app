import { useEffect, useRef } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";

interface LiDARViewerProps {
  /** Array of ranges in meters */
  ranges: number[];
  angleMin?: number;
  angleMax?: number;
  rangeMax?: number;
}

export function LiDARViewer({
  ranges,
  angleMin = -Math.PI,
  angleMax = Math.PI,
  rangeMax = 12,
}: LiDARViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || ranges.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const scale = Math.min(cx, cy) * 0.85 / rangeMax;

    ctx.clearRect(0, 0, w, h);

    // Grid circles
    ctx.strokeStyle = "rgba(100,100,100,0.3)";
    ctx.lineWidth = 0.5;
    for (let r = 2; r <= rangeMax; r += 2) {
      ctx.beginPath();
      ctx.arc(cx, cy, r * scale, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Cross
    ctx.beginPath();
    ctx.moveTo(cx, 0);
    ctx.lineTo(cx, h);
    ctx.moveTo(0, cy);
    ctx.lineTo(w, cy);
    ctx.stroke();

    // Robot
    ctx.fillStyle = "#3b82f6";
    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, Math.PI * 2);
    ctx.fill();

    // Points
    const angleStep = (angleMax - angleMin) / ranges.length;
    ctx.fillStyle = "#ef4444";
    for (let i = 0; i < ranges.length; i++) {
      const r = ranges[i];
      if (r <= 0 || r >= rangeMax) continue;
      const angle = angleMin + i * angleStep - Math.PI / 2;
      const px = cx + Math.cos(angle) * r * scale;
      const py = cy + Math.sin(angle) * r * scale;
      ctx.beginPath();
      ctx.arc(px, py, 1.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [ranges, angleMin, angleMax, rangeMax]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">LiDAR</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-center">
        <canvas
          ref={canvasRef}
          width={300}
          height={300}
          className="rounded-lg bg-black/5 dark:bg-white/5"
        />
      </CardContent>
    </Card>
  );
}
