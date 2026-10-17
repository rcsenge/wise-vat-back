// The globe script renders a painted 3D globe with orbiting gold coins.
import * as THREE from "./vendor/globe/three.module.js";

const GLOBE_ROTATION_RADIANS_PER_SECOND = 0.12;
const GLOBE_TILT_RADIANS = 0.12;
const ORBIT_RADIANS_PER_SECOND = 0.45;
const ORBIT_RADIUS = 1.32;
const ORBIT_TILT_RADIANS = -0.42;
const COIN_SPIN_RADIANS_PER_SECOND = 2.2;
const COIN_RADIUS = 0.17;
const COIN_THICKNESS = 0.035;
const COIN_GROUP_OFFSETS = [0, Math.PI];
const COINS_PER_GROUP = 4;
const COIN_SPACING_RADIANS = 0.24;
const TEXTURE_WIDTH = 4096;
const TEXTURE_HEIGHT = 2048;
const PAINT_STROKE_COUNT = 9000;
const PIXEL_RATIO_LIMIT = 2;

// The palette paints the illustration. The UI colors stay in the Tailwind theme.
const OCEAN_COLORS = ["#1f5fc4", "#2a7fd8", "#1c9aa6", "#3fb0c9", "#164c9e"];
const LAND_COLORS = ["#3f9f5a", "#6cc06a", "#2c8a6a", "#9fd27a", "#4fb39a"];
const GOLD_COLOR = "#f6b93b";
const GOLD_DARK_COLOR = "#d08e1f";
const GOLD_LIGHT_COLOR = "#ffd77a";

const canvasElement = document.getElementById("countdown-globe");

function pickRandom(items) {
  return items[Math.floor(Math.random() * items.length)];
}

// The function converts a longitude and latitude to a texture point.
function projectPoint([longitude, latitude]) {
  return [
    ((longitude + 180) / 360) * TEXTURE_WIDTH,
    ((90 - latitude) / 180) * TEXTURE_HEIGHT,
  ];
}

function createLandPath(land) {
  const path = new Path2D();
  for (const feature of land.features) {
    const geometry = feature.geometry;
    const polygons =
      geometry.type === "Polygon"
        ? [geometry.coordinates]
        : geometry.coordinates;
    for (const rings of polygons) {
      for (const ring of rings) {
        ring.forEach((point, index) => {
          const [x, y] = projectPoint(point);
          if (index === 0) {
            path.moveTo(x, y);
            return;
          }
          path.lineTo(x, y);
        });
        path.closePath();
      }
    }
  }
  return path;
}

// The function paints soft round strokes to imitate a painted surface.
function paintStrokes(context, colors) {
  for (let index = 0; index < PAINT_STROKE_COUNT; index += 1) {
    context.globalAlpha = 0.08 + Math.random() * 0.22;
    context.fillStyle = pickRandom(colors);
    const y = Math.random() * TEXTURE_HEIGHT;
    const latitude = (0.5 - y / TEXTURE_HEIGHT) * Math.PI;
    // The stretch keeps strokes round on the sphere near the poles.
    const stretch = 1 / Math.max(Math.cos(latitude), 0.04);
    context.beginPath();
    context.ellipse(
      Math.random() * TEXTURE_WIDTH,
      y,
      (12 + Math.random() * 70) * stretch,
      6 + Math.random() * 30,
      0,
      0,
      Math.PI * 2,
    );
    context.fill();
  }
  context.globalAlpha = 1;
}

async function createGlobeTexture() {
  const response = await fetch("vendor/globe/land-50m.json");
  if (!response.ok) {
    throw new Error(`The map data request failed: ${response.status}`);
  }
  const topology = await response.json();
  const landPath = createLandPath(
    window.topojson.feature(topology, topology.objects.land),
  );

  const textureCanvas = document.createElement("canvas");
  textureCanvas.width = TEXTURE_WIDTH;
  textureCanvas.height = TEXTURE_HEIGHT;
  const context = textureCanvas.getContext("2d");

  context.fillStyle = OCEAN_COLORS[1];
  context.fillRect(0, 0, TEXTURE_WIDTH, TEXTURE_HEIGHT);
  paintStrokes(context, OCEAN_COLORS);

  context.save();
  context.clip(landPath, "evenodd");
  context.fillStyle = LAND_COLORS[0];
  context.fillRect(0, 0, TEXTURE_WIDTH, TEXTURE_HEIGHT);
  paintStrokes(context, LAND_COLORS);
  context.restore();

  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  return texture;
}

function createCoinFaceTexture() {
  const size = 512;
  const faceCanvas = document.createElement("canvas");
  faceCanvas.width = size;
  faceCanvas.height = size;
  const context = faceCanvas.getContext("2d");
  const center = size / 2;

  context.fillStyle = GOLD_COLOR;
  context.fillRect(0, 0, size, size);
  context.lineWidth = size * 0.05;
  context.strokeStyle = GOLD_DARK_COLOR;
  context.beginPath();
  context.arc(center, center, size * 0.4, 0, Math.PI * 2);
  context.stroke();

  context.font = `900 ${size * 0.5}px Inter, sans-serif`;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillStyle = GOLD_DARK_COLOR;
  context.fillText("€", center + size * 0.015, center + size * 0.035);
  context.fillStyle = GOLD_LIGHT_COLOR;
  context.fillText("€", center, center + size * 0.02);

  const texture = new THREE.CanvasTexture(faceCanvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

// The function builds one coin from an open edge ring and two face discs.
function createCoinTemplate() {
  const edgeGeometry = new THREE.CylinderGeometry(
    COIN_RADIUS,
    COIN_RADIUS,
    COIN_THICKNESS,
    64,
    1,
    true,
  );
  edgeGeometry.rotateX(Math.PI / 2);
  const edge = new THREE.Mesh(
    edgeGeometry,
    new THREE.MeshStandardMaterial({
      color: GOLD_DARK_COLOR,
      emissive: GOLD_DARK_COLOR,
      emissiveIntensity: 0.25,
      metalness: 0.35,
      roughness: 0.35,
    }),
  );

  const faceGeometry = new THREE.CircleGeometry(COIN_RADIUS, 64);
  const faceMaterial = new THREE.MeshStandardMaterial({
    map: createCoinFaceTexture(),
    emissive: GOLD_COLOR,
    emissiveIntensity: 0.25,
    metalness: 0.25,
    roughness: 0.4,
  });
  const frontFace = new THREE.Mesh(faceGeometry, faceMaterial);
  frontFace.position.z = COIN_THICKNESS / 2;
  const backFace = new THREE.Mesh(faceGeometry, faceMaterial);
  backFace.position.z = -COIN_THICKNESS / 2;
  backFace.rotation.y = Math.PI;

  const coin = new THREE.Group();
  coin.add(edge, frontFace, backFace);
  return coin;
}

function createCoins() {
  const template = createCoinTemplate();
  const coins = [];
  for (const groupOffset of COIN_GROUP_OFFSETS) {
    for (let index = 0; index < COINS_PER_GROUP; index += 1) {
      const coin = template.clone();
      coin.userData.orbitOffset = groupOffset + index * COIN_SPACING_RADIANS;
      coin.userData.spinOffset = index * 0.9;
      coins.push(coin);
    }
  }
  return coins;
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
  camera.position.set(0, 0, 6.2);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x223a10, 1.4));
  const sunLight = new THREE.DirectionalLight(0xfff4e0, 2.6);
  sunLight.position.set(-3, 3, 4);
  scene.add(sunLight);
  const rimLight = new THREE.DirectionalLight(0x9fe870, 1.2);
  rimLight.position.set(4, -1, -2);
  scene.add(rimLight);

  const globe = new THREE.Mesh(
    new THREE.SphereGeometry(1, 128, 128),
    new THREE.MeshStandardMaterial({
      map: await createGlobeTexture(),
      roughness: 0.65,
      metalness: 0,
    }),
  );
  globe.rotation.x = GLOBE_TILT_RADIANS;
  scene.add(globe);

  const orbit = new THREE.Group();
  orbit.rotation.z = ORBIT_TILT_RADIANS;
  orbit.rotation.x = 0.28;
  scene.add(orbit);
  const coins = createCoins();
  coins.forEach((coin) => orbit.add(coin));

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
    const seconds = timeMilliseconds / 1000;
    globe.rotation.y = seconds * GLOBE_ROTATION_RADIANS_PER_SECOND;
    for (const coin of coins) {
      const angle =
        seconds * ORBIT_RADIANS_PER_SECOND + coin.userData.orbitOffset;
      coin.position.set(
        Math.cos(angle) * ORBIT_RADIUS,
        0,
        Math.sin(angle) * ORBIT_RADIUS,
      );
      coin.rotation.y =
        seconds * COIN_SPIN_RADIANS_PER_SECOND + coin.userData.spinOffset;
    }
    renderer.render(scene, camera);
  });
}

startGlobe().catch((error) => {
  console.error("The globe failed to start.", error);
  canvasElement.remove();
});
