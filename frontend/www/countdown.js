// The countdown page shows the money that the world loses in five minutes.
"use strict";

const COUNTDOWN_DURATION_SECONDS = 300;
const COUNTDOWN_TICK_MILLISECONDS = 100;
const LOSS_PER_YEAR_EUR = 20_000_000_000;
const SECONDS_PER_YEAR = 365 * 24 * 60 * 60;
const LOSS_PER_SECOND_EUR = LOSS_PER_YEAR_EUR / SECONDS_PER_YEAR;

const timerElement = document.getElementById("countdown-timer");
const progressElement = document.getElementById("countdown-progress");
const lossElement = document.getElementById("countdown-loss");
const startButton = document.getElementById("countdown-button-start");
const resetButton = document.getElementById("countdown-button-reset");

const euroFormat = new Intl.NumberFormat("en-IE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

let intervalId = null;
let startTimestamp = 0;
let elapsedBeforePauseMilliseconds = 0;

// The function returns the elapsed time. The value stops at the duration.
function readElapsedSeconds() {
  const runningMilliseconds =
    intervalId === null ? 0 : Date.now() - startTimestamp;
  const elapsedSeconds =
    (elapsedBeforePauseMilliseconds + runningMilliseconds) / 1000;
  return Math.min(elapsedSeconds, COUNTDOWN_DURATION_SECONDS);
}

function render(elapsedSeconds) {
  const remainingSeconds = Math.ceil(
    COUNTDOWN_DURATION_SECONDS - elapsedSeconds,
  );
  const minutes = String(Math.floor(remainingSeconds / 60)).padStart(2, "0");
  const seconds = String(remainingSeconds % 60).padStart(2, "0");
  timerElement.textContent = `${minutes}:${seconds}`;
  progressElement.value = elapsedSeconds;
  lossElement.textContent = euroFormat.format(
    elapsedSeconds * LOSS_PER_SECOND_EUR,
  );
}

function stopInterval() {
  clearInterval(intervalId);
  intervalId = null;
}

function tick() {
  const elapsedSeconds = readElapsedSeconds();
  render(elapsedSeconds);
  if (elapsedSeconds < COUNTDOWN_DURATION_SECONDS) {
    return;
  }
  elapsedBeforePauseMilliseconds = COUNTDOWN_DURATION_SECONDS * 1000;
  stopInterval();
  startButton.textContent = "Done";
  startButton.disabled = true;
}

function pause() {
  elapsedBeforePauseMilliseconds += Date.now() - startTimestamp;
  stopInterval();
  startButton.textContent = "Resume";
}

function start() {
  startTimestamp = Date.now();
  intervalId = setInterval(tick, COUNTDOWN_TICK_MILLISECONDS);
  startButton.textContent = "Pause";
}

startButton.addEventListener("click", () => {
  if (intervalId === null) {
    start();
    return;
  }
  pause();
});

resetButton.addEventListener("click", () => {
  stopInterval();
  elapsedBeforePauseMilliseconds = 0;
  startButton.textContent = "Start";
  startButton.disabled = false;
  render(0);
});

render(0);
