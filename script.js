const API_BASE = '';
let muted = false;

// ══════════════════════════════════════════
// STARFIELD
// ══════════════════════════════════════════
const starsEl = document.getElementById('stars');
for (let i = 0; i < 110; i++) {
  const s = document.createElement('div');
  s.className = 'star';
  const sz = Math.random() * 2.5 + .5;
  Object.assign(s.style, {
    width: sz+'px', height: sz+'px',
    left: Math.random()*100+'%', top: Math.random()*100+'%',
    animationDelay: (Math.random()*5)+'s',
    animationDuration: (2+Math.random()*4)+'s',
  });
  starsEl.appendChild(s);
}

// ══════════════════════════════════════════
// WEBCAM
// ══════════════════════════════════════════
const video      = document.getElementById('webcam');
const snapCanvas = document.getElementById('snapshot');
const flashEl    = document.getElementById('flash-overlay');

async function startWebcam() {
  try {
    video.srcObject = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user' },
      audio: false,
    });
    await video.play();
  } catch {
    setBubble("Camera access needed — please allow and reload.");
  }
}

// ══════════════════════════════════════════
// SPEECH SYNTHESIS
// ══════════════════════════════════════════
function setAvatarSpeed(speed) {
  const player = document.getElementById('avatar-lottie');
  if (player) player.setSpeed(speed);
}

function speak(text, onDone) {
  setBubble(text);
  if (muted) { if (onDone) onDone(); return; }
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 0.9; u.pitch = 1.2;
  const voices = speechSynthesis.getVoices();
  const pick = voices.find(v =>
    ['Samantha','Karen','Daniel','Google UK English Female'].some(n => v.name.includes(n))
  );
  if (pick) u.voice = pick;
  u.onstart = () => setAvatarSpeed(2);
  u.onend   = () => {
    setAvatarSpeed(1);
    if (onDone) onDone();
  };
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

function setBubble(text) { document.getElementById('bubble-text').textContent = text; }

// ══════════════════════════════════════════
// SPEECH RECOGNITION
// ══════════════════════════════════════════
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
if (SR) {
  recognition = new SR();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';
}

function extractOccupation(text) {
  return text.toLowerCase()
    .replace(/i (want|would like|plan) to (be|become) (an? )?/gi, '')
    .replace(/i('m| am) going to be (an? )?/gi, '')
    .replace(/^(be|become) (an? )?/gi, '')
    .replace(/^(a|an) (good|great|amazing|fantastic|wonderful|brilliant|successful|bad|nice) /gi, '')
    .replace(/^(good|great|amazing|fantastic|wonderful|brilliant|successful) /gi, '')
    .replace(/^(a|an) /i, '').trim();
}

function startListening() {
  if (!recognition) {
    document.getElementById('text-fallback').style.display = 'block';
    setBubble("Type your dream career below!");
    return;
  }
  const mic = document.getElementById('mic-badge');
  mic.style.display = 'flex';
  mic.classList.add('mic-pulse');
  setBubble("I'm listening… what's your dream career?");

  let gotResult = false;

  function showTextFallback() {
    hideMic();
    document.getElementById('text-fallback').style.display = 'block';
    setBubble("Type your dream career below!");
  }

  // iOS doesn't auto-stop after silence — force fallback after 7 s
  const listenTimeout = setTimeout(() => {
    if (!gotResult) { try { recognition.stop(); } catch(e) {} showTextFallback(); }
  }, 7000);

  try { recognition.abort(); } catch(e) {}
  try { recognition.start(); } catch(e) { clearTimeout(listenTimeout); showTextFallback(); return; }

  recognition.onresult = e => {
    clearTimeout(listenTimeout);
    gotResult = true;
    hideMic();
    handleOccupation(extractOccupation(e.results[0][0].transcript));
  };
  recognition.onerror = () => {
    clearTimeout(listenTimeout);
    hideMic();
    document.getElementById('text-fallback').style.display = 'block';
    setBubble("Mic didn't catch that — type below!");
  };
  recognition.onend = () => {
    clearTimeout(listenTimeout);
    hideMic();
    if (!gotResult) showTextFallback();
  };
}

function hideMic() {
  const m = document.getElementById('mic-badge');
  m.style.display = 'none'; m.classList.remove('mic-pulse');
}

function submitTextInput() {
  const val = document.getElementById('text-input').value.trim();
  if (!val) return;
  document.getElementById('text-fallback').style.display = 'none';
  handleOccupation(val);
}
document.getElementById('text-input').addEventListener('keydown', e => { if (e.key==='Enter') submitTextInput(); });

// ══════════════════════════════════════════
// COUNTDOWN  3 … 2 … 1 … 📸
// ══════════════════════════════════════════
async function countdown() {
  const screen = document.getElementById('countdown-screen');
  const numEl  = document.getElementById('countdown-num');
  screen.style.display = 'flex';
  for (const n of ['3','2','1','📸']) {
    numEl.textContent = n;
    numEl.style.animation = 'none';
    void numEl.offsetWidth;          // reflow to restart animation
    numEl.style.animation = 'countPulse .85s ease-in-out forwards';
    await delay(850);
  }
  screen.style.display = 'none';
}

// ══════════════════════════════════════════
// CAPTURE
// ══════════════════════════════════════════
async function capturePhoto() {
  await countdown();
  // White flash
  flashEl.style.transition = 'none';
  flashEl.style.opacity = '0.95';
  await delay(70);
  flashEl.style.transition = 'opacity .6s ease';
  flashEl.style.opacity = '0';
  // Match canvas to actual video dimensions so portrait/landscape never compresses the face
  snapCanvas.width  = video.videoWidth;
  snapCanvas.height = video.videoHeight;
  const ctx = snapCanvas.getContext('2d');
  ctx.save();
  ctx.scale(-1, 1);
  ctx.drawImage(video, -snapCanvas.width, 0, snapCanvas.width, snapCanvas.height);
  ctx.restore();
  // Show thumbnail in loading panel
  document.getElementById('snap-thumb').src = snapCanvas.toDataURL('image/jpeg', .7);
  return snapCanvas.toDataURL('image/jpeg', .85).split(',')[1];
}

// ══════════════════════════════════════════
// CONFETTI
// ══════════════════════════════════════════
function launchConfetti() {
  const cc = document.getElementById('confetti-canvas');
  cc.width = window.innerWidth; cc.height = window.innerHeight;
  cc.style.display = 'block';
  const ctx = cc.getContext('2d');
  const colors = ['#fde68a','#f9a8d4','#a78bfa','#34d399','#60a5fa','#fb923c','#f472b6'];
  const pieces = Array.from({length:200}, () => ({
    x: Math.random()*cc.width, y: -20 - Math.random()*180,
    w: Math.random()*12+5, h: Math.random()*6+3,
    color: colors[Math.floor(Math.random()*colors.length)],
    vx: (Math.random()-.5)*6, vy: Math.random()*3+2,
    rot: Math.random()*360, rv: (Math.random()-.5)*9,
  }));
  let t = 0;
  (function draw() {
    ctx.clearRect(0,0,cc.width,cc.height);
    pieces.forEach(p => {
      p.x+=p.vx; p.y+=p.vy; p.rot+=p.rv; p.vy+=.07;
      ctx.save(); ctx.translate(p.x+p.w/2, p.y+p.h/2); ctx.rotate(p.rot*Math.PI/180);
      ctx.fillStyle=p.color; ctx.fillRect(-p.w/2,-p.h/2,p.w,p.h); ctx.restore();
    });
    if (++t < 240) requestAnimationFrame(draw);
    else cc.style.display='none';
  })();
}

// ══════════════════════════════════════════
// SPELL CASTING
// ══════════════════════════════════════════
let sparkleTimer;

function startSpellCasting() {
  document.querySelector('.avatar-orb').classList.add('spell-casting');
  setAvatarSpeed(3);
  sparkleTimer = setInterval(spawnSparkle, 120);
}

function stopSpellCasting() {
  document.querySelector('.avatar-orb').classList.remove('spell-casting');
  setAvatarSpeed(1);
  clearInterval(sparkleTimer);
}

function spawnSparkle() {
  const orb = document.querySelector('.avatar-orb');
  if (!orb) return;
  const emojis = ['✨','⭐','💫','🌟','✦'];
  const s = document.createElement('span');
  s.className = 'sparkle';
  const angle = Math.random() * Math.PI * 2;
  const dist = 60 + Math.random() * 80;
  Object.assign(s.style, {
    left: (30 + Math.random() * 100) + 'px',
    top:  (30 + Math.random() * 100) + 'px',
    fontSize: (12 + Math.random() * 12) + 'px',
  });
  s.textContent = emojis[Math.floor(Math.random() * emojis.length)];
  orb.appendChild(s);
  requestAnimationFrame(() => {
    s.style.transform = `translate(${Math.cos(angle)*dist}px, ${Math.sin(angle)*dist}px) scale(0)`;
    s.style.opacity = '0';
  });
  setTimeout(() => s.remove(), 1050);
}

// ══════════════════════════════════════════
// MAIN FLOW
// ══════════════════════════════════════════
async function handleOccupation(occupation) {
  if (!occupation) {
    speak("Didn't catch that — type your dream career in the box below!");
    document.getElementById('text-fallback').style.display = 'block';
    return;
  }

  speak(`A ${occupation}? Brilliant! Get ready for your photo!`);
  await delay(1800);

  const base64 = await capturePhoto();

  document.getElementById('camera-container').style.display  = 'none';
  document.getElementById('loading-container').style.display = 'flex';
  document.getElementById('result-container').style.display  = 'none';
  speak(`Creating your future as a ${occupation}… stand by!`);
  startSpellCasting();

  let data;
  try {
    const res = await fetch(API_BASE + '/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: base64, occupation }),
    });
    data = await res.json();
  } catch {
    stopSpellCasting();
    speak("Network error. Let's try again!", () => resetApp()); return;
  }

  if (data.error === 'blocked') {
    stopSpellCasting();
    document.getElementById('loading-container').style.display = 'none';
    document.getElementById('camera-container').style.display  = 'block';
    speak("Let's pick a real career! Try doctor, astronaut, or teacher.", () => startListening());
    return;
  }
  if (data.error) { stopSpellCasting(); speak("Something went wrong. Let's try again!", () => resetApp()); return; }

  // Pre-load image so we never flash the old/empty image
  const img = new Image();
  img.onload  = () => showResult(data.image_url, data.occupation || occupation);
  img.onerror = () => { stopSpellCasting(); speak("Couldn't load result. Let's try again!", () => resetApp()); };
  img.src = data.image_url;
}

function showResult(imageUrl, occupation) {
  stopSpellCasting();
  document.getElementById('loading-container').style.display = 'none';

  const img = document.getElementById('result-image');
  img.src = imageUrl;                       // already cached — no flicker

  // Re-trigger flip animation
  const wrap = img.parentElement;
  wrap.classList.remove('flip-reveal');
  void wrap.offsetWidth;
  wrap.classList.add('flip-reveal');

  document.getElementById('result-container').style.display = 'flex';
  document.getElementById('occupation-label').textContent = occupation;
  document.getElementById('occupation-badge').style.display = 'block';
  setAvatarSpeed(3);

  launchConfetti();
  setTimeout(() => speak(`Here you are as a ${occupation}! You look absolutely incredible!`), 700);
}

function resetApp() {
  stopSpellCasting();
  document.getElementById('camera-container').style.display  = 'block';
  document.getElementById('loading-container').style.display = 'none';
  document.getElementById('result-container').style.display  = 'none';
  document.getElementById('occupation-badge').style.display  = 'none';
  document.getElementById('text-fallback').style.display     = 'none';
  document.getElementById('text-input').value = '';
  setAvatarSpeed(1);
  start();
}

// ══════════════════════════════════════════
// BOOT
// ══════════════════════════════════════════
const delay = ms => new Promise(r => setTimeout(r, ms));

async function start() {
  await delay(500);
  speak(
    "Hi! I'm Cosmo, your career guide! Look at the camera and tell me — what do you want to be when you grow up?",
    () => setTimeout(startListening, 400)
  );
}

// After player is ready, re-enforce seamless looping on the internal lottie instance
document.getElementById('avatar-lottie').addEventListener('ready', () => {
  const lottie = document.getElementById('avatar-lottie').getLottie();
  if (lottie) { lottie.loop = true; lottie.goToAndPlay(0, true); }
});


// ══════════════════════════════════════════
// PASSWORD
// ══════════════════════════════════════════
async function submitPassword() {
  const val = document.getElementById('password-input').value;
  const err = document.getElementById('password-error');
  const btn = document.getElementById('start-btn');
  if (!val.trim()) return;
  btn.disabled = true;
  try {
    const res = await fetch('/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: val }),
    });
    if (res.ok) {
      document.getElementById('start-overlay').style.display = 'none';
      err.style.display = 'none';
      startWebcam();
      start();
    } else {
      err.style.display = 'block';
      document.getElementById('password-input').value = '';
      btn.disabled = false;
    }
  } catch {
    err.textContent = 'Network error — try again';
    err.style.display = 'block';
    btn.disabled = false;
  }
}
document.getElementById('start-btn').addEventListener('click', submitPassword);
document.getElementById('password-input').addEventListener('keydown', e => { if (e.key === 'Enter') submitPassword(); });

// ══════════════════════════════════════════
// MUTE
// ══════════════════════════════════════════
document.getElementById('mute-btn').addEventListener('click', () => {
  muted = !muted;
  document.getElementById('mute-btn').textContent = muted ? '🔇' : '🔊';
  if (muted) speechSynthesis.cancel();
});
