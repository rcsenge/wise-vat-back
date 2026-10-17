// The globe script renders a slowly rotating 3D globe on the countdown page.
import * as THREE from "./vendor/globe/three.module.js";

const ROTATION_RADIANS_PER_SECOND = 0.12;
const AXIS_TILT_RADIANS = 0.38;
const TEXTURE_WIDTH = 4096;
const TEXTURE_HEIGHT = 2048;
const PIXEL_RATIO_LIMIT = 2;

const canvasElement = document.getElementById("countdown-globe");
const rootStyle = getComputedStyle(document.documentElement);
const oceanColor = rootStyle
  .getPropertyValue("--color-brand-bright-green")
  .trim();
const landColor = rootStyle
  .getPropertyValue("--color-brand-forest-green")
  .trim();

// The function converts a longitude and latitude to a texture point.
function projectPoint([longitude, latitude]) {
  return [
    ((longitude + 180) / 360) * TEXTURE_WIDTH,
    ((90 - latitude) / 180) * TEXTURE_HEIGHT,
  ];
}

function drawPolygon(context, rings) {
  context.beginPath();
  for (const ring of rings) {
    ring.forEach((point, index) => {
      const [x, y] = projectPoint(point);
      if (index === 0) {
        context.moveTo(x, y);
        return;
      }
      context.lineTo(x, y);
    });
    context.closePath();
  }
  context.fill("evenodd");
}

async function createGlobeTexture() {
  const response = await fetch("vendor/globe/land-50m.json");
  if (!response.ok) {
    throw new Error(`The map data request failed: ${response.status}`);
  }
  const topology = await response.json();
  const land = window.topojson.feature(topology, topology.objects.land);

  const textureCanvas = document.createElement("canvas");
  textureCanvas.width = TEXTURE_WIDTH;
  textureCanvas.height = TEXTURE_HEIGHT;
  const context = textureCanvas.getContext("2d");
  context.fillStyle = oceanColor;
  context.fillRect(0, 0, TEXTURE_WIDTH, TEXTURE_HEIGHT);
  context.fillStyle = landColor;
  for (const feature of land.features) {
    const geometry = feature.geometry;
    const polygons =
      geometry.type === "Polygon"
        ? [geometry.coordinates]
        : geometry.coordinates;
    polygons.forEach((rings) => drawPolygon(context, rings));
  }

  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  return texture;
}

async function startGlobe() {
  const renderer = new THREE.WebGLRenderer({
    canvas: canvasElement,
    antialias: true,
    alpha: true,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, PIXEL_RATIO_LIMIT));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
  camera.position.set(0, 0, 4.3);

  scene.add(new THREE.HemisphereLight(0xffffff, 0xd8e6cf, 1.6));
  const sunLight = new THREE.DirectionalLight(0xffffff, 2.4);
  sunLight.position.set(-3, 2.5, 4);
  scene.add(sunLight);

  const material = new THREE.MeshStandardMaterial({
    map: await createGlobeTexture(),
    roughness: 0.5,
    metalness: 0,
  });
  const globe = new THREE.Mesh(new THREE.SphereGeometry(1, 128, 128), material);
  globe.rotation.x = AXIS_TILT_RADIANS;
  scene.add(globe);

  function resize() {
    const width = canvasElement.clientWidth;
    const height = canvasElement.clientHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(canvasElement);
  resize();

  renderer.setAnimationLoop((timeMilliseconds) => {
    globe.rotation.y = (timeMilliseconds / 1000) * ROTATION_RADIANS_PER_SECOND;
    renderer.render(scene, camera);
  });
}

startGlobe().catch((error) => {
  console.error("The globe failed to start.", error);
  canvasElement.remove();
});
