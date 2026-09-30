# Setup and demo publishing

## Desktop experience

Tested on Windows with Unreal Engine 5.8.3. Assets saved with this version should not be opened or saved in an older engine. The current release is an editor-backed desktop prototype, not a packaged standalone executable.

```powershell
git lfs install
git clone https://github.com/samguan2020/guans-fencing-club.git
cd guans-fencing-club
git lfs pull
```

Open `GuansFencingClub.uproject` with the installed UE 5.8 editor. Alternatively, set the `UE_EDITOR` environment variable to your `UnrealEditor.exe` path and run `Play.cmd` or `OpenEditor.cmd`. The launchers fall back to the original machine's engine location if the variable is absent.

In the game: W/A/S/D to move, mouse to look, Space to jump, Alt+F4 to close. In editor Play: Esc to stop, Shift+F1 to release the mouse.

## Reconstruction

The runtime assets are included; rebuilding is optional. Back up manual changes first. Run UE scripts in the editor's Python environment, not ordinary system Python.

1. `build_ue_hall.py`: replaces the base map from `SourceAssets/Hall/fencing_hall.fbx`.
2. `add_duel.py`, then `align_duel.py`: imports both FBXs and aligns the replay.
3. `add_tv_sabres.py`: adds the wall display and sabres.
4. `sample_sword_tips.py`: samples current tip positions in editor Play.
5. Run `SourceAssets/build_tip_trails.py` with Blender, then `add_tip_trails.py` in UE.
6. Run `validate_tip_trails.py` in an editor session to verify the integrated playback.

Use Blender 3.6 for the supplied geometry-generation scripts. Source hall files are in `SourceAssets/Hall`. `SourceAssets/extract_video_frames.py` regenerates the padded 250-frame video sequence from `Content/Movies/fencing_duel_clip.mp4`.

DeepMotion generation occurs upstream and is not automated by this repository. The project consumes two already generated FBXs; generating replacements requires your own account and suitable source footage. Trail sampling must be repeated after animation or placement changes.

## Preview this website

From the project root:

```powershell
python -m http.server 8000 --directory docs
```

Open http://localhost:8000. No build step, package installation, or external font service is required. The website is a case study, not a browser port of Unreal Engine.

## Add your demo video

1. Put a browser-compatible MP4 (H.264 video, optional AAC audio) at `docs/assets/demo.mp4`.
2. Change `demoVideo` in `docs/site-config.js` from `''` to `'assets/demo.mp4'`.
3. Preview locally, commit both files, and push to `main`.

The page will show a native video player with pause, seek, and fullscreen controls. Until configured, it shows an honest “video will be added” message and the existing screenshots. A direct public HTTPS video URL can also be used.

Keep website video outside Git LFS: GitHub Pages does not serve LFS objects directly. For a large recording, use an external video host rather than committing a large MP4. GitHub blocks regular Git files above 100 MiB. See [GitHub file limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) and [LFS limitations](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).

The Pages workflow deploys only `docs/` on changes to that folder. Repository Settings → Pages should use GitHub Actions. Core project binaries use Git LFS, while website images remain ordinary Git files.

[Original Chinese walkthrough guide](local-guide-zh.md)
