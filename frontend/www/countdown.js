// The countdown page shows a growing euro amount during five minutes.
"use strict";

const COUNTDOWN_DURATION_SECONDS = 300;
const LOSS_PER_YEAR_EUR = 20_000_000_000;
const SECONDS_PER_YEAR = 365 * 24 * 60 * 60;
const LOSS_PER_SECOND_EUR = LOSS_PER_YEAR_EUR / SECONDS_PER_YEAR;

const timerElement = document.getElementById("countdown-timer");
const progressElement = document.getElementById("countdown-progress");
const amountElement = document.getElementById("countdown-amount");
const startButton = document.getElementById("countdown-button-start");
const resetButton = document.getElementById("countdown-button-reset");

const amountFormat = new Intl.NumberFormat("en-IE", {
  maximumFractionDigits: 0,
});

let isRunning = false;
let animationFrameId = null;
let startTimestamp = 0;
let elapsedBeforePauseMilliseconds = 0;

// The function returns the elapsed time in milliseconds. The value stops at the duration.
function readElapsedMilliseconds() {
  const runningMilliseconds = isRunning
    ? performance.now() - startTimestamp
    : 0;
  return Math.min(
    elapsedBeforePauseMilliseconds + runningMilliseconds,
    COUNTDOWN_DURATION_SECONDS * 1000,
  );
}

function render(elapsedMilliseconds) {
  const remainingMilliseconds =
    COUNTDOWN_DURATION_SECONDS * 1000 - elapsedMilliseconds;
  const integerSeconds = Math.floor(remainingMilliseconds / 1000);
  const tenths = Math.floor((remainingMilliseconds % 1000) / 100);
  const minutes = String(Math.floor(integerSeconds / 60)).padStart(2, "0");
  const seconds = String(integerSeconds % 60).padStart(2, "0");
  timerElement.textContent = `${minutes}:${seconds}.${tenths}`;
  const elapsedSeconds = elapsedMilliseconds / 1000;
  progressElement.value = elapsedSeconds;
  amountElement.textContent = amountFormat.format(
    elapsedSeconds * LOSS_PER_SECOND_EUR,
  );
}

function requestNextFrame() {
  animationFrameId = requestAnimationFrame(tick);
}

function tick() {
  const elapsedMilliseconds = readElapsedMilliseconds();
  render(elapsedMilliseconds);
  if (elapsedMilliseconds < COUNTDOWN_DURATION_SECONDS * 1000) {
    requestNextFrame();
    return;
  }
  elapsedBeforePauseMilliseconds = COUNTDOWN_DURATION_SECONDS * 1000;
  isRunning = false;
  startButton.textContent = "Done";
  startButton.disabled = true;
}

function stopAnimation() {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId);
  }
  animationFrameId = null;
  isRunning = false;
}

function pause() {
  elapsedBeforePauseMilliseconds += performance.now() - startTimestamp;
  stopAnimation();
  startButton.textContent = "Resume";
}

function start() {
  isRunning = true;
  startTimestamp = performance.now();
  requestNextFrame();
  startButton.textContent = "Pause";
}

startButton.addEventListener("click", () => {
  if (isRunning) {
    pause();
    return;
  }
  start();
});

resetButton.addEventListener("click", () => {
  stopAnimation();
  elapsedBeforePauseMilliseconds = 0;
  startButton.textContent = "Start";
  startButton.disabled = false;
  render(0);
});

render(0);
