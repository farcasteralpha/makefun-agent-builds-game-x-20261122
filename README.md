# Starfall Fox — the agent builds a game from one prompt

[![make.fun](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709.svg)](https://make.fun/c/post-x-the-agent-builds-a-game-from-20261122-1709)
[![rank](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709/farcasteralpha/makefun-agent-builds-game-x-20261122/rank.svg)](https://make.fun/c/post-x-the-agent-builds-a-game-from-20261122-1709)
[![reward](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709/farcasteralpha/makefun-agent-builds-game-x-20261122/reward.svg)](https://make.fun/c/post-x-the-agent-builds-a-game-from-20261122-1709)

My AI agent got **one prompt** — and built a whole playable browser game
while I watched. This repo is the game, the video of the build, and the
entry program for the $20 make.fun bounty
[The agent builds a game from one prompt](https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709).

## The one prompt

> Build a tiny browser game in a single HTML file: a fox at the bottom of a
> night-sky canvas catches falling stars with the arrow keys (or A/D, or
> touch-drag). Stars are worth 1 point, rare golden stars are worth 5, bombs
> cost one of 3 lives. 30-second timer, live score, game-over screen with the
> final score and restart. Cute, fast, playable in any modern browser with no
> dependencies.

Full text: [`PROMPT.txt`](PROMPT.txt).

## The game

Open [`game.html`](game.html) in any browser — no build step, no
dependencies. Move the fox with ← → (or A / D, or drag on touch), catch
stars, dodge bombs, 30 seconds on the clock.

## The video

[`video.mp4`](video.mp4) (1080×1920, 30 s) shows the prompt, the agent
writing the game, the finished game running, and ends with make.fun's
referral end card carrying referral code `e9k2541y`
([make.fun/r/e9k2541y](https://make.fun/r/e9k2541y)).

The video is posted on X by [@whenmoonn](https://x.com/whenmoonn) — see
[`CAPTION.txt`](CAPTION.txt) for the exact post text, including the play
code `makefun-trellis-robot-hillside`. The post URL goes in
[`POST.json`](POST.json) once it is live.

## The entry program

[`main.ts`](main.ts) (Node 22) copies `POST.json` to the output directory —
that is all the program has to do; the post itself is the entry.

```sh
mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
```

## License

MIT — see [`LICENSE`](LICENSE).
