import { useEffect, useRef } from 'react';
import type { FaceResponse } from '../api';

interface Props {
  imageUrl: string;
  faces: FaceResponse[];
}

export function FaceOverlay({ imageUrl, faces }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;

    const draw = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      ctx.drawImage(img, 0, 0);

      for (const face of faces) {
        const [x1, y1, x2, y2] = face.detection.bbox;
        const w = x2 - x1;
        const h = y2 - y1;

        // Bounding box
        const isLive = face.liveness?.is_live;
        const color = isLive === false ? '#ef4444' : isLive === true ? '#22c55e' : '#6366f1';
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(2, Math.min(canvas.width, canvas.height) * 0.003);
        ctx.strokeRect(x1, y1, w, h);

        // Label background
        const labels: string[] = [];
        if (face.demographics?.age) labels.push(`${face.demographics.gender || ''}${face.demographics.age}`);
        if (face.quality) labels.push(`Q:${face.quality.overall_score.toFixed(0)}`);
        if (face.liveness) labels.push(face.liveness.is_live ? 'LIVE' : 'SPOOF');
        labels.push(`${(face.detection.confidence * 100).toFixed(0)}%`);

        const text = labels.join(' | ');
        const fontSize = Math.max(12, Math.min(canvas.width, canvas.height) * 0.018);
        ctx.font = `bold ${fontSize}px system-ui`;
        const metrics = ctx.measureText(text);
        const pad = 4;

        ctx.fillStyle = color;
        ctx.fillRect(x1, y1 - fontSize - pad * 2, metrics.width + pad * 2, fontSize + pad * 2);

        ctx.fillStyle = '#fff';
        ctx.fillText(text, x1 + pad, y1 - pad);

        // Landmarks
        ctx.fillStyle = '#22d3ee';
        for (const [lx, ly] of face.detection.landmarks) {
          ctx.beginPath();
          ctx.arc(lx, ly, Math.max(2, canvas.width * 0.003), 0, Math.PI * 2);
          ctx.fill();
        }
      }
    };

    if (img.complete) draw();
    else img.onload = draw;
  }, [imageUrl, faces]);

  return (
    <div className="relative">
      <img ref={imgRef} src={imageUrl} alt="" className="hidden" />
      <canvas ref={canvasRef} className="w-full rounded-lg" />
    </div>
  );
}
