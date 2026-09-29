import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Polyline3D } from "../api";
import { useTheme } from "@/components/theme-provider";
import { Card } from "@/components/ui/card";

/** Piece colors are chosen for white paper; lift the dark ones so they read on a dark canvas. */
function lineColor(hex: string, dark: boolean): THREE.Color {
  const c = new THREE.Color(hex);
  if (dark) {
    const hsl = { h: 0, s: 0, l: 0 };
    c.getHSL(hsl);
    if (hsl.l < 0.6) c.setHSL(hsl.h, hsl.s, 0.6 + hsl.l * 0.3);
  }
  return c;
}

/** Shows every piece standing in place, so you can see the finished frame. */
export default function Viewer3D({ model }: { model: Polyline3D[] }) {
  const dark = useTheme().resolvedTheme === "dark";
  const host = useRef<HTMLDivElement>(null);
  const view = useRef<{ camera: THREE.PerspectiveCamera; controls: OrbitControls; fitted: boolean } | null>(null);
  const scene = useRef(new THREE.Scene());
  const group = useRef<THREE.Group | null>(null);

  // One-time renderer setup.
  useEffect(() => {
    const el = host.current!;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    el.appendChild(renderer.domElement);
    const camera = new THREE.PerspectiveCamera(40, 1, 1, 10_000);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    view.current = { camera, controls, fitted: false };

    const resize = () => {
      const { clientWidth: w, clientHeight: h } = el;
      renderer.setSize(w, h);
      camera.aspect = w / Math.max(h, 1);
      camera.updateProjectionMatrix();
    };
    const ro = new ResizeObserver(resize);
    ro.observe(el);
    resize();

    let frame = 0;
    const tick = () => {
      controls.update();
      renderer.render(scene.current, camera);
      frame = requestAnimationFrame(tick);
    };
    tick();
    return () => {
      cancelAnimationFrame(frame);
      ro.disconnect();
      controls.dispose();
      renderer.dispose();
      el.removeChild(renderer.domElement);
      view.current = null;
    };
  }, []);

  // Rebuild the lines whenever the template or theme changes.
  useEffect(() => {
    if (group.current) {
      scene.current.remove(group.current);
      group.current.traverse((o) => {
        if (o instanceof THREE.LineLoop) {
          o.geometry.dispose();
          (o.material as THREE.Material).dispose();
        }
      });
    }
    const g = new THREE.Group();
    for (const line of model) {
      const geom = new THREE.BufferGeometry().setFromPoints(line.pts.map(([x, y, z]) => new THREE.Vector3(x, y, z)));
      g.add(new THREE.LineLoop(geom, new THREE.LineBasicMaterial({ color: lineColor(line.color, dark) })));
    }
    scene.current.add(g);
    group.current = g;

    if (view.current && !view.current.fitted) {
      view.current.fitted = true;
      const sphere = new THREE.Box3().setFromObject(g).getBoundingSphere(new THREE.Sphere());
      const { camera, controls } = view.current;
      const dist = (sphere.radius / Math.sin((camera.fov * Math.PI) / 360)) * 1.1;
      camera.position.copy(sphere.center).add(new THREE.Vector3(0.8, 0.35, 1).normalize().multiplyScalar(dist));
      controls.target.copy(sphere.center);
    }
  }, [model, dark]);

  return (
    <Card className="gap-0 py-0">
      <div ref={host} className="h-[min(70vh,640px)] cursor-grab active:cursor-grabbing" />
      <p className="border-t px-4 py-2.5 text-xs text-muted-foreground">
        Drag to rotate · scroll to zoom · right-drag to pan
      </p>
    </Card>
  );
}
