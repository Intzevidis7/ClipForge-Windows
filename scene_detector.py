
"""Hard-cut scene detection so clip boundaries land on clean cuts, using PySceneDetect."""
from typing import List
import sys


def detect_scene_boundaries(video_path: str, threshold: float = 27.0) -> List[float]:
    """Return sorted list of timestamps (seconds) where scene cuts occur, including 0 and video end."""
    from scenedetect import open_video, SceneManager
    from scenedetect.detectors import ContentDetector

    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))

    total_frames = video.duration.get_frames() if video.duration else None

    def _progress(frame_num):
        if total_frames:
            pct = min(int((frame_num / total_frames) * 100), 100)
            bar_width = 40
            filled = int(bar_width * pct / 100)
            bar = "#" * filled + "-" * (bar_width - filled)
            sys.stdout.write(f"\r  [{bar}] {pct:3d}%")
            sys.stdout.flush()

    scene_manager.detect_scenes(video, show_progress=False, callback=lambda frame, frame_num: _progress(frame_num))
    print()
    scene_list = scene_manager.get_scene_list()

    boundaries = [0.0]
    for start, end in scene_list:
        boundaries.append(end.get_seconds())
    return sorted(set(boundaries))


def snap_to_nearest_boundary(t: float, boundaries: List[float], max_shift: float = 2.0) -> float:
    if not boundaries:
        return t
    nearest = min(boundaries, key=lambda b: abs(b - t))
    if abs(nearest - t) <= max_shift:
        return nearest
    return t
