# One Pace Organizer

This program organizes One Pace videos for Plex, Jellyfin, Emby, and Kodi. Mode 0 renames videos and writes local NFO files; Plex modes update metadata through the Plex API. Console, headless, and desktop GUI versions are available. [See the upstream wiki](https://github.com/ladyisatis/OnePaceOrganizer/wiki) for setup instructions.

Mode 0 writes `tvshow.nfo` and a matching `.nfo` for each episode, even when artwork is unavailable or poster fetching is disabled. It keeps `season.nfo` and available artwork in season folders for Jellyfin and Emby. For Kodi, it writes arc names and descriptions into `tvshow.nfo` and copies available season artwork to the show folder as `season01-poster.png` and `season01-fanart.png` (or `season-specials-*` for specials). Kodi v22+ reads arc descriptions from `<seasonplot>`.

Kodi reads episode numbers from video filenames, not NFO files. The default filenames contain `SxxEyy`; if you use metadata-only mode or change the filename template, keep that pattern. The show title and sort title are **One Pace** even when upstream metadata calls it One Piece. Arc and episode titles remain unchanged. Episode runtimes in NFO files are in minutes.

Re-run the program after new releases. Existing NFO files are preserved unless `overwrite_nfo` is enabled. Enable it when updating a library that already has NFO files titled One Piece, then refresh the existing Kodi or Jellyfin library entries to reload the changed files.

On a rerun, files named with the default `One Pace - SxxEyy - Title.mkv` pattern are matched by their season, episode, and current title (including `(Extended)`). They do not need to match a current release hash. Files with changed or custom titles still use the original hash lookup and may be skipped. When only the name matches, the organizer uses the latest non-archived release's metadata for that episode; its release date or runtime may differ from an older cut.

The organizer does not require a complete collection. For a newly released episode without published metadata, it attempts to read metadata from the MKV.

## Metadata

Metadata is sourced from [one-pace-metadata](https://github.com/ladyisatis/one-pace-metadata?tab=readme-ov-file#one-pace-metadata).

## Contributing

Contributions via Pull Requests are always welcome if I miss a bug or want another feature added in, want to contribute a program icon, etc.

## Thanks

- Craigy (@verywittyname on Discord) for Episode Descriptions spreadsheets and updates
- Barry (@yogobarry on Discord) and his Jellyfin metadata set for One Pace series description, tvshow information (genres) etc.
- [SpykerNZ/one-pace-for-plex](https://github.com/SpykerNZ/one-pace-for-plex) for NFO setup
  - and unofficial posters in the *posters* directory (which were also done by [/u/piratezekk](https://www.reddit.com/user/piratezekk))
- [matteron/one-pace-plex-api](https://github.com/matteron/one-pace-plex-api) for the code that updates the Plex API
- [IconArchive](https://www.iconarchive.com/show/one-piece-jolly-roger-icons-by-crountch/Luffys-flag-icon.html) for application icon
- The [One Pace Team](https://onepace.net/) itself for:
  - [Official posters](https://github.com/ladyisatis/one-pace-metadata/tree/main/posters) present in the Episode Guide
  - One Pace Episode Guide spreadsheet managing, which amalgamates into [data.json](https://raw.githubusercontent.com/ladyisatis/one-pace-metadata/refs/heads/main/data.json)
  - Fantastic edits and for getting the group I watch One Piece with through without losing their minds
