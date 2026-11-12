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
    # long, loop'un tam katıdır: hedef süreyi karşılayan en küçük kat
    total_s = math.ceil(ep.duration_s / loop_len - 1e-9) * loop_len
    rendered = audio.render(ep, work, total_s)
    video.build_long(ep, loop, rendered.path, total_s, out / "long.mp4")
    short_info = short.build_short(ep, rendered, out / "short.mp4", work)
    metadata.write(ep, Path(args.episode_dir), out, rendered, loop_len, total_s, short_info)
    print(f"{out}/long.mp4 ({total_s:.0f} sn), {out}/short.mp4, {out}/metadata.json")
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

    p = sub.add_parser("build", help="episode'u build et: long.mp4, short.mp4, metadata.json")
    p.add_argument("episode_dir")
    p.add_argument("--duration", help="hedef süreyi ez (örn. 10m); deneme build'i içindir")
    p.set_defaults(func=_build)

    p = sub.add_parser("qc", help="output/<slug> çıktısını ölç, qc.json yaz")
    p.add_argument("output_dir")
    p.set_defaults(func=_qc)

    p = sub.add_parser("synth", help="episode'un eksik klip/ses girdilerini sentetik üret (deneme)")
    p.add_argument("episode_dir")
    p.set_defaults(func=_synth)

    p = sub.add_parser("doctor", help="üretime hazırlık kontrolü")
    p.set_defaults(func=_doctor)

    args = parser.parse_args(argv)
    return args.func(args)
