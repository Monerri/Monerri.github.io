"""Adds voiceover and background music to the silent renders.

    python audio.py MODEL_DIR

Reads  out/silent/*.mp4  (from render.js), writes  out/*.mp4.
Voice: Kokoro TTS (Apache 2.0), British English. MODEL_DIR must hold kokoro-v1.0.onnx and
voices-v1.0.bin from https://github.com/thewh1teagle/kokoro-onnx/releases
Needs: pip install kokoro-onnx numpy scipy soundfile, plus ffmpeg.
Music: an original bed synthesised below, so there is nothing to license.
"""
import subprocess, sys, pathlib
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, fftconvolve
from kokoro_onnx import Kokoro

SR, LEN = 44100, 32.0
VOICE, SPEED = "bf_emma", 1.0
HERE = pathlib.Path(__file__).parent

# (earliest start in seconds, line). Lines never overlap: a late line is pushed back.
HOOKS = {
    "master": "Make your home better, with the right people.",
    "variation-1-gamble": "Finding a tradesperson you can trust shouldn't be a gamble.",
    "variation-2-who-do-you-call": "New windows. A new kitchen. An extension. But who do you call?",
    "variation-3-four-checks": "Before we recommend anyone, they pass four checks.",
}
BODY = [
    (4.7, "Vetted North matches you with a trusted local specialist."),
    (8.1, "It's three simple steps."),
    (9.7, "Tell us what you need."),
    (11.3, "We find a suitable specialist."),
    (13.6, "Then they contact you, and you'll know who to expect."),
    (17.1, "Every specialist passes four checks before we recommend them."),
    (21.2, "And we review them regularly."),
    (23.9, "It's free, you choose how many get in touch, and there's no obligation."),
    (28.5, "Start your project at vetted north dot com."),
]


def speak(kokoro, text):
    samples, sr = kokoro.create(text, voice=VOICE, speed=SPEED, lang="en-gb")
    samples = resample_poly(samples, SR, sr).astype(np.float64)
    loud = np.flatnonzero(np.abs(samples) > 0.01)  # trim leading and trailing silence
    return samples[max(0, loud[0] - 400): loud[-1] + 2000]


def voice_track(kokoro, hook):
    track, cursor = np.zeros(int(LEN * SR)), 0.0
    for start, text in [(0.5, hook)] + BODY:
        clip = speak(kokoro, text)
        at = max(start, cursor + 0.3)
        end = at + len(clip) / SR
        print(f"  {at:5.2f}-{end:5.2f}  {text}")
        if end > LEN:
            raise SystemExit("voiceover runs past the end of the video")
        i = int(at * SR)
        track[i:i + len(clip)] += clip
        cursor = end
    return track / np.abs(track).max() * 0.85


# ---------------------------------------------------------------- music bed
def note(freq, dur, kind):
    t = np.arange(int(dur * SR)) / SR
    if kind == "keys":   # soft electric-piano: a few decaying partials
        w = sum(a * np.sin(2 * np.pi * freq * h * t) * np.exp(-t * d)
                for h, a, d in [(1, 1, 1.6), (2, .35, 2.6), (3, .12, 4), (4, .05, 6)])
        w *= np.minimum(1, t / .008)
    elif kind == "pad":  # slow, slightly detuned sines
        w = sum(np.sin(2 * np.pi * freq * k * t) for k in (.997, 1, 1.003)) / 3
        w *= np.minimum(1, t / .9) * np.minimum(1, (dur - t) / .9)
    else:                # bass: rounded sine
        w = np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.2) * np.minimum(1, t / .02)
    return w * np.minimum(1, (dur - t) / .05)


def music():
    hz = lambda midi: 440 * 2 ** ((midi - 69) / 12)
    bars, bar = 11, LEN / 11          # 11 bars of 4 beats, about 82 bpm
    beat = bar / 4
    C, Am, F, G = [48, 55, 60, 62, 64], [45, 52, 57, 60, 64], [41, 53, 57, 60, 64], [43, 55, 59, 62, 67]
    prog = [C, Am, F, G, C, Am, F, G, F, G, C]
    arp = [1, 2, 3, 4, 3, 2, 3, 4]    # eighth-note pattern over chord tones
    out = np.zeros((int((LEN + 4) * SR), 2))

    def add(w, at, gain, pan=0.0):
        i = int(at * SR)
        out[i:i + len(w), 0] += w * gain * (1 - pan) / 2 * 2 ** .5
        out[i:i + len(w), 1] += w * gain * (1 + pan) / 2 * 2 ** .5

    for b, chord in enumerate(prog):
        t0, last = b * bar, b == bars - 1
        for m in chord[1:]:
            add(note(hz(m), bar + .8, "pad"), t0, .10)
        add(note(hz(chord[0]), bar, "bass"), t0, .32)
        if not last:
            add(note(hz(chord[0]), beat * 1.5, "bass"), t0 + beat * 2.5, .20)
        for m in chord[1:4]:          # chord on the downbeat
            add(note(hz(m), bar, "keys"), t0, .16)
        if last:                      # let the final chord ring
            add(note(hz(72), 4, "keys"), t0 + beat, .22)
            continue
        for k, idx in enumerate(arp):
            add(note(hz(chord[idx] + 12), beat * 1.5, "keys"), t0 + k * beat / 2,
                .13 if k % 2 else .17, pan=(-.35, .35)[k % 2])

    rng = np.random.default_rng(7)    # simple reverb: decaying noise impulse
    tail = np.arange(int(1.8 * SR)) / SR
    wet = np.stack([fftconvolve(out[:, c], rng.standard_normal(len(tail)) * np.exp(-tail * 3.2))
                    [:len(out)] for c in (0, 1)], axis=1)
    mix = (out + wet * .012)[:int(LEN * SR)]
    t = np.arange(len(mix)) / SR
    mix *= (np.minimum(1, t / .6) * np.minimum(1, (LEN - t) / 2.2))[:, None]
    return mix / np.abs(mix).max()


def duck(voice):
    """Music gain curve: full in the gaps, lower while the voice is speaking."""
    win = int(.25 * SR)
    env = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
    speaking = np.clip(env / .04, 0, 1)
    smooth = np.convolve(speaking, np.hanning(int(.5 * SR)) / np.hanning(int(.5 * SR)).sum(), "same")
    return .27 - .17 * smooth


def main(model_dir):
    kokoro = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    bed = music()
    for name, hook in HOOKS.items():
        print(name)
        voice = voice_track(kokoro, hook)
        mix = bed * duck(voice)[:, None] + voice[:, None]
        mix = mix / np.abs(mix).max() * 10 ** (-1 / 20)
        wav = HERE / "out" / f"{name}.wav"
        sf.write(wav, mix, SR, subtype="PCM_16")
        stem = f"vetted-north-explainer-{name}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", HERE / "out" / "silent" / stem, "-i", wav,
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                        HERE / "out" / stem], check=True)
        wav.unlink()


if __name__ == "__main__":
    main(sys.argv[1])
