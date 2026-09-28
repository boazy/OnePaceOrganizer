import sqlite3
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import aiosqlite

from src.organizer import OnePaceOrganizer


class RenamedFilesTest(unittest.IsolatedAsyncioTestCase):
    async def test_rerun_recognizes_previous_names_without_matching_wrong_cut(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "episodes.db"
            with sqlite3.connect(db_path) as conn:
                conn.executescript("""
                    CREATE TABLE arcs (id INTEGER, lang TEXT, part INTEGER, saga TEXT,
                        title TEXT, originaltitle TEXT, description TEXT);
                    CREATE TABLE descriptions (lang TEXT, arc INTEGER, episode INTEGER,
                        title TEXT, originaltitle TEXT, description TEXT);
                    CREATE TABLE episodes (id INTEGER, arc INTEGER, episode INTEGER,
                        manga_chapters TEXT, anime_episodes TEXT, released TEXT,
                        duration INTEGER, extended INTEGER, archived INTEGER,
                        hash_crc32 TEXT, hash_blake2s TEXT, file_name TEXT);
                    CREATE TABLE other_edits (id INTEGER, hash_crc32 TEXT, hash_blake2s TEXT);
                    INSERT INTO arcs VALUES (6, 'en', 6, 'East Blue', 'Arlong Park', '', 'Luffy meets Arlong.');
                    INSERT INTO descriptions VALUES ('en', 6, 2,
                        'Monsters of the Grand Line', '', 'The crew meets the fishmen.');
                    INSERT INTO descriptions VALUES ('en', 6, 5,
                        'Live', '', 'The crew survives.');
                """)
                conn.executemany(
                    "INSERT INTO episodes VALUES (?, 6, ?, '', '', ?, ?, ?, ?, ?, '', ?)",
                    [
                        (1, 2, '2020-01-01', 1200, 0, 1, 'OLD00001', 'old-release.mkv'),
                        (2, 2, '2025-01-01', 1322, 0, 0, 'NEW00002', 'new-release.mkv'),
                        (3, 5, '2025-01-01', 1000, 0, 0, 'STANDARD', 'standard.mkv'),
                        (4, 5, '2025-01-02', 1500, 1, 0, 'EXTENDED', 'extended.mkv'),
                    ],
                )

            input_path = root / "downloads"
            output_path = root / "One Pace"
            input_path.mkdir()
            output_path.mkdir()
            for filename in (
                "One Pace - S06E02 - Monsters of the Grand Line.mkv",
                "One Pace - S06E05 - Live (Extended).mkv",
                "One Pace - S06E02 - Alternate Cut.mkv",
            ):
                (input_path / filename).write_bytes(filename.encode())

            organizer = OnePaceOrganizer()
            organizer.base_path = root
            organizer.input_path = input_path
            organizer.output_path = output_path
            organizer.store.tvshow = {"title": "One Piece", "sorttitle": "One Piece", "customrating": "TV-14"}
            organizer.store.conn = await aiosqlite.connect(db_path)
            organizer.store.conn.row_factory = aiosqlite.Row
            organizer.opened = True
            organizer.fetch_posters = False
            organizer.file_action = 1
            organizer.progress_bar_func = lambda _: None
            try:
                found = await organizer.glob_video_files()
                accepted = [entry for entry in found if entry[0] == 0]
                self.assertEqual(len(accepted), 2)
                self.assertEqual(
                    [entry[2].name for entry in found if entry[0] == 3],
                    ["One Pace - S06E02 - Alternate Cut.mkv"],
                )

                completed, skipped = await organizer.process_nfo(found)
                self.assertEqual((completed, skipped), (2, 1))
                season_path = output_path / "Season 06"
                standard = ET.parse(
                    season_path / "One Pace - S06E02 - Monsters of the Grand Line.nfo"
                ).getroot()
                extended = ET.parse(season_path / "One Pace - S06E05 - Live (Extended).nfo").getroot()
                self.assertEqual(standard.findtext("runtime"), "22")
                self.assertEqual(extended.findtext("title"), "Live (Extended)")
                self.assertEqual(extended.findtext("runtime"), "25")
                self.assertFalse((season_path / "One Pace - S06E02 - Alternate Cut.mkv").exists())
            finally:
                await organizer.store.close()


if __name__ == "__main__":
    unittest.main()
