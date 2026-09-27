import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.organizer import OnePaceOrganizer


class SampleMetadata:
    tvshow = {
        "title": "One Piece",
        "sorttitle": "One Piece",
        "originaltitle": "One Pace",
        "customrating": "TV-14",
        "plot": "Edited to match the manga.",
    }
    arcs = {
        0: {"part": 0, "title": "Specials", "saga": "Extras", "description": "Bonus edits."},
        1: {"part": 1, "title": "Romance Dawn", "saga": "East Blue", "description": "Luffy sets sail."},
    }
    episodes = {
        "special": {"arc": 0, "episode": 1, "title": "Bonus", "description": "A bonus edit.", "duration": 61},
        "romance": {
            "arc": 1, "episode": 1, "title": "The Beginning",
            "description": "The first edit.", "duration": 1077,
        },
    }

    async def get_arcs(self):
        return list(self.arcs.values())

    async def get_arc(self, part):
        return self.arcs[part]

    async def get_episode(self, id, with_descriptions=False):
        return self.episodes[id]


class NfoCompatibilityTest(unittest.IsolatedAsyncioTestCase):
    async def test_one_pace_show_and_arc_metadata_work_for_both_readers(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            input_path = root / "downloads"
            output_path = root / "One Pace"
            input_path.mkdir()
            output_path.mkdir()
            for season in (0, 1):
                poster = root / "posters" / str(season) / "poster.png"
                poster.parent.mkdir(parents=True)
                poster.write_bytes(f"poster {season}".encode())
                background = poster.with_name("background.png")
                background.write_bytes(f"background {season}".encode())
            (root / "posters" / "poster.png").write_bytes(b"show poster")

            videos = []
            for id in ("special", "romance"):
                video = input_path / f"{id}.mkv"
                video.write_bytes(f"video {id}".encode())
                videos.append((0, id, video, None))

            organizer = OnePaceOrganizer()
            organizer.base_path = root
            organizer.input_path = input_path
            organizer.output_path = output_path
            organizer.store = SampleMetadata()
            organizer.fetch_posters = False
            organizer.file_action = 1  # Copy so downloads remain untouched.
            organizer.progress_bar_func = lambda _: None

            completed, skipped = await organizer.process_nfo(videos)
            self.assertEqual((completed, skipped), (2, 0))

            show = ET.parse(output_path / "tvshow.nfo").getroot()
            self.assertEqual(show.findtext("title"), "One Pace")
            self.assertEqual(show.findtext("sorttitle"), "One Pace")
            self.assertEqual(show.findtext("originaltitle"), "One Pace")
            self.assertEqual(show.find("uniqueid").attrib["type"], "onepace")
            self.assertEqual(
                {item.attrib["number"]: item.text for item in show.findall("namedseason")},
                {"0": "Specials", "1": "1. Romance Dawn"},
            )
            self.assertEqual(
                {item.attrib["number"]: item.text for item in show.findall("seasonplot")},
                {"0": "Bonus edits.", "1": "Luffy sets sail."},
            )

            for number, folder, title, plot, runtime in (
                (0, "Specials", "Bonus", "A bonus edit.", "1"),
                (1, "Season 01", "The Beginning", "The first edit.", "18"),
            ):
                basename = f"One Pace - S{number:02d}E01 - {title}"
                season_path = output_path / folder
                self.assertTrue((season_path / f"{basename}.mkv").is_file())
                episode = ET.parse(season_path / f"{basename}.nfo").getroot()
                self.assertEqual(episode.findtext("title"), title)
                self.assertEqual(episode.findtext("showtitle"), "One Pace")
                self.assertEqual(episode.findtext("plot"), plot)
                self.assertEqual(episode.findtext("runtime"), runtime)
                self.assertEqual(episode.findtext("season"), str(number))
                self.assertEqual(episode.findtext("episode"), "1")
                self.assertEqual(episode.find("uniqueid").attrib["type"], "onepace")

                jellyfin = ET.parse(season_path / "season.nfo").getroot()
                self.assertEqual(jellyfin.findtext("plot"), SampleMetadata.arcs[number]["description"])
                kodi_prefix = "season-specials" if number == 0 else f"season{number:02d}"
                for artwork in ("poster", "fanart"):
                    kodi_art = output_path / f"{kodi_prefix}-{artwork}.png"
                    jellyfin_art = Path(jellyfin.findtext(f"art/{artwork}"))
                    self.assertTrue(jellyfin_art.is_file())
                    self.assertEqual(kodi_art.read_bytes(), jellyfin_art.read_bytes())


    async def test_nfo_generation_without_artwork(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            input_path = root / "downloads"
            output_path = root / "One Pace"
            input_path.mkdir()
            output_path.mkdir()
            video = input_path / "romance.mkv"
            video.write_bytes(b"video")

            organizer = OnePaceOrganizer()
            organizer.base_path = root
            organizer.input_path = input_path
            organizer.output_path = output_path
            organizer.store = SampleMetadata()
            organizer.fetch_posters = False
            organizer.file_action = 1
            organizer.progress_bar_func = lambda _: None

            completed, skipped = await organizer.process_nfo([(0, "romance", video, None)])
            self.assertEqual((completed, skipped), (1, 0))
            show = ET.parse(output_path / "tvshow.nfo").getroot()
            self.assertEqual(show.findtext("title"), "One Pace")
            self.assertIsNone(show.find("art"))
            season_path = output_path / "Season 01"
            self.assertEqual(ET.parse(season_path / "season.nfo").getroot().findtext("plot"), "Luffy sets sail.")
            episode_path = season_path / "One Pace - S01E01 - The Beginning.nfo"
            self.assertEqual(ET.parse(episode_path).getroot().findtext("showtitle"), "One Pace")
            self.assertFalse((output_path / "season01-poster.png").exists())


if __name__ == "__main__":
    unittest.main()
