"""`python -m pipeline {build,qc,check,synth,doctor}`"""

import argparse
import math
import sys
from pathlib import Path

from pydantic import ValidationError

from pipeline.config import CONFIG, load_episode

TRIAL_DURATION = "10m"  # long enough to cross several loop seams, short enough to build in a minute


def _report(problems: list[str]) -> bool:
    if problems:
        print("missing inputs:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("to try the flow with synthetic inputs: build <episode> --trial", file=sys.stderr)
    return bool(problems)


def _build(args: argparse.Namespace) -> int:
    from pipeline import audio, ffmpeg, metadata, preflight, short, synth, video

    duration = args.duration or (TRIAL_DURATION if args.trial else None)
    ep = load_episode(args.episode_dir, duration)
    if args.trial:
        synth.run(ep)
    if _report(preflight.problems(ep)):
        return 1
    out = Path("output") / ep.slug
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)
    (out / "qc.json").unlink(missing_ok=True)  # the old verdict does not describe this build

    loop = video.encode_loop(ep, work)
    loop_len = ffmpeg.duration(loop)
    # the long is an exact multiple of the loop: the smallest multiple that meets the target
    total_s = math.ceil(ep.duration_s / loop_len - 1e-9) * loop_len
    rendered = audio.render(ep, work, total_s)
    video.build_long(ep, loop, rendered.path, total_s, out / "long.mp4")
    short_info = short.build_short(ep, rendered, out / "short.mp4", work)
    video.thumbnail(loop, out / "thumbnail.jpg")
    episode_dir = Path(args.episode_dir)
    metadata.write(ep, episode_dir, out, rendered, loop_len, total_s, short_info, args.trial)
    print(f"{out}/long.mp4 ({total_s:.0f} s), short.mp4, thumbnail.jpg, metadata.json")
    if args.trial:
        print("TRIAL build: synthetic inputs and/or shortened duration; not for upload")
    return 0


def _qc(args: argparse.Namespace) -> int:
    from pipeline import qc

    return qc.run(Path(args.output_dir))


def _check(args: argparse.Namespace) -> int:
    from pipeline import preflight

    if _report(preflight.problems(load_episode(args.episode_dir))):
        return 1
    print("config valid, all inputs present")
    return 0


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
    p.add_argument("--duration", help="override the target duration (e.g. 10m)")
    p.add_argument(
        "--trial",
        action="store_true",
        help=f"try the flow: synthesize missing inputs, build only {TRIAL_DURATION}",
    )
    p.set_defaults(func=_build)

    p = sub.add_parser("qc", help="measure the output/<slug> output, write qc.json")
    p.add_argument("output_dir")
    p.set_defaults(func=_qc)

    p = sub.add_parser("check", help="validate episode.yaml and list every missing input")
    p.add_argument("episode_dir")
    p.set_defaults(func=_check)

    p = sub.add_parser("synth", help="synthesize the episode's missing clip/audio inputs (trial)")
    p.add_argument("episode_dir")
    p.set_defaults(func=_synth)

    p = sub.add_parser("doctor", help="production readiness check")
    p.set_defaults(func=_doctor)

    args = parser.parse_args(argv)
    if not CONFIG.is_dir():
        print("error: run from the repository root (config/ not found here)", file=sys.stderr)
        return 2
    try:
        return args.func(args)
    except ValidationError as e:
        lines = [f"  - {'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
        print("error: invalid episode/brand config\n" + "\n".join(lines), file=sys.stderr)
    except (FileNotFoundError, ValueError) as e:  # user-fixable input problems: no traceback
        print(f"error: {e}", file=sys.stderr)
    return 2
