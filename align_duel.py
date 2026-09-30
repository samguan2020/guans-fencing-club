"""Constrain reconstructed lateral drift to piste 1 using non-destructive actor tracks."""
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve()
data=json.loads((ROOT/'SourceAssets/Duel/placement_input.json').read_text())
report=json.loads((ROOT/'duel_setup.json').read_text())
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
levels.load_level('/Game/GuansClub/FencingHall')
seq=u.load_asset('/Game/GuansClub/Duel/LS_Piste01_Duel')
for binding in seq.get_bindings():
    idx=str(binding.get_name()).split()[-1]
    info=next(d for d in data if d['id']==idx)
    for t in list(binding.get_tracks()):
        if isinstance(t,u.MovieScene3DTransformTrack): binding.remove_track(t)
    tr=binding.add_track(u.MovieScene3DTransformTrack)
    sec=tr.add_section()
    sec.set_range(0,250)
    channels=sec.get_all_channels()
    u.log('DUEL_CHANNELS '+str([(c.get_name(),str(c.get_class())) for c in channels]))
    for c,val in zip(channels,[report['x_offset_cm'],310+info['median_y_m']*100,7.5,0,0,0,1,1,1]): c.set_default(val)
    for f,y in enumerate(info['lateral_y_m']):
        channels[1].add_key(u.FrameNumber(f),310+100*y,interpolation=u.MovieSceneKeyInterpolation.LINEAR)
report['notes'][1]='Per-frame actor Y offset cancels reconstructed lateral root drift; hip centres stay on piste 1. Original poses and longitudinal root motion are unchanged.'
report['lateral_alignment']='animated actor transform; no changes to source FBX'
(ROOT/'duel_setup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.EditorAssetLibrary.save_loaded_asset(seq)
levels.save_current_level()
u.log('DUEL_ALIGNMENT_COMPLETE')
