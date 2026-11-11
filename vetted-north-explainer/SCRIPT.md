# Vetted North explainer: script

32 seconds, 1920x1080, 30 fps, with background music and no voiceover. On-screen text carries the message.
All claims are taken from vettednorth.com as it stood on 11 November 2026.

| Time | Scene | On screen | Voiceover (currently off) |
|---|---|---|---|
| 0.0 – 4.0 | Hook | Opening line (see below) beside the home photo | Opening line |
| 4.0 – 7.5 | Brand | Logo builds, tick draws in. "We match you with a trusted local specialist who's right for your home." | Vetted North matches you with a trusted local specialist. |
| 7.5 – 16.5 | How it works | "Three simple steps". 1 Tell us what you need. 2 We find a suitable specialist. 3 They contact you, and we tell you who they are first. | It's three simple steps. Tell us what you need. We find a suitable specialist. Then they contact you, and you'll know who to expect. |
| 16.5 – 23.5 | Trust | "Four checks before we recommend anyone": registered company, insurance-backed guarantee, trade scheme registration, Google rating above four stars. | Every specialist passes four checks before we recommend them. And we review them regularly. |
| 23.5 – 27.5 | Control | "You stay in control." Free for homeowners. 1, 2 or 3 specialists, you choose. No obligation. | It's free, you choose how many get in touch, and there's no obligation. |
| 27.5 – 32.0 | Call to action | "Make your home better. With the right people." Find a specialist, vettednorth.com | Start your project at vettednorth.com. |

## Opening lines

| File | First line | Angle |
|---|---|---|
| `out/vetted-north-explainer-master.mp4` | Make your home better. With the right people. | Aspiration (the site headline) |
| `out/vetted-north-explainer-variation-1-gamble.mp4` | Finding a tradesperson you can trust shouldn't be a gamble. | Pain point |
| `out/vetted-north-explainer-variation-2-who-do-you-call.mp4` | New windows. A new kitchen. An extension. But who do you call? | Question / project-led |
| `out/vetted-north-explainer-variation-3-four-checks.mp4` | Before we recommend anyone, they pass four checks. | Proof-led |

## Audio

- Voice: switched off. To bring it back, set `VOICEOVER = True` in `audio.py`. It uses Kokoro text-to-speech (open source, Apache 2.0), British English voice `bf_emma`. Change `VOICE` in `audio.py` to try `bf_alice`, `bf_isabella`, `bf_lily`, `bm_george`, `bm_daniel`, `bm_lewis` or `bm_fable`.
- Music: an original bed (soft keys, pad and bass in C major, about 82 bpm) synthesised in `audio.py`, so there is nothing to license. It dips automatically under the voice when the voiceover is on.

## Rebuilding

- Preview the visuals: open `index.html` in a browser (`?v=1`, `?v=2`, `?v=3` for the variations).
- Edit on-screen opening lines in the `HOOKS` array at the bottom of `index.html`; edit spoken lines and their timings at the top of `audio.py`.
- Render visuals: `node render.js` (needs Playwright with Chromium, and ffmpeg). Writes `out/silent/`, about three and a half minutes.
- Add audio: `python audio.py` (setup notes are at the top of the file). Writes `out/`.
