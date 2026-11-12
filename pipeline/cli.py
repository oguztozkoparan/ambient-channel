"""`python -m pipeline {build,qc,synth,doctor}`"""

import argparse
import math
from pathlib import Path

from pipeline.config import load_episode


def _build(args: argparse.Namespace) -> int:
    from pipeline import audio, ffmpeg, metadata, short, video

    ep = load_episode(args.episode_dir, args.duration)
    out = Path("output") / ep.slug
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)

    loop = video.encode_loop(ep, work)
    loop_len = ffmpeg.duration(loop)
    # the long is an exact multiple of the loop: the smallest multiple that meets the target
    total_s = math.ceil(ep.duration_s / loop_len - 1e-9) * loop_len
    rendered = audio.render(ep, work, total_s)
    video.build_long(ep, loop, rendered.path, total_s, out / "long.mp4")
    short_info = short.build_short(ep, rendered, out / "short.mp4", work)
    metadata.write(ep, Path(args.episode_dir), out, rendered, loop_len, total_s, short_info)
    print(f"{out}/long.mp4 ({total_s:.0f} s), {out}/short.mp4, {out}/metadata.json")
    return 0


def _qc(args: argparse.Namespace) -> int:
    from pipeline import qc

    return qc.run(Path(args.output_dir))


def _synth(args: argparse.Namespace) -> int:
    from pipeline import synth

    return synth.run(load_episode(args.episode_dir))


def _doctor(_: argparse.Namespace) -> int:
    from pipeline import doctor

    return doctor.run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("build", help="build the episode: long.mp4, short.mp4, metadata.json")
    p.add_argument("episode_dir")
    p.add_argument("--duration", help="override the target duration (e.g. 10m); for trial builds")
    p.set_defaults(func=_build)

    p = sub.add_parser("qc", help="measure the output/<slug> output, write qc.json")
    p.add_argument("output_dir")
    p.set_defaults(func=_qc)

    p = sub.add_parser("synth", help="synthesize the episode's missing clip/audio inputs (trial)")
    p.add_argument("episode_dir")
    p.set_defaults(func=_synth)

    p = sub.add_parser("doctor", help="production readiness check")
    p.set_defaults(func=_doctor)

    args = parser.parse_args(argv)
    return args.func(args)
