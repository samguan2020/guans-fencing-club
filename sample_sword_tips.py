import unreal as u,time,json,traceback
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve()
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
levels.load_level('/Game/GuansClub/FencingHall')
u.EditorPythonScripting.set_keep_python_script_alive(True)
levels.editor_request_begin_play()
state={'start':time.monotonic(),'phase':'start','i':0,'samples':[]}
def end(error=None):
    (ROOT/'SourceAssets/tip_samples.json').write_text(json.dumps({'error':error,'fps':48,'samples':state['samples']},indent=2))
    u.log('TIP_SAMPLING_COMPLETE '+str(error))
    u.unregister_slate_post_tick_callback(handle);levels.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
    try:
        if state['phase']=='start':
            if time.monotonic()-state['start']<4:return
            world=ed.get_game_world()
            replay=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.LevelSequenceActor) if 'GuansDuel' in map(str,a.tags))
            state['player']=replay.get_editor_property('sequence_player');state['player'].pause()
            state['swords']=sorted([a for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor) if a.get_actor_label().endswith(' - Sabre')],key=lambda a:a.get_actor_label())
            assert len(state['swords'])==2
            state['phase']='seek'
        elif state['phase']=='seek':
            p=u.MovieSceneSequencePlaybackParams()
            p.set_editor_property('position_type',u.MovieScenePositionType.FRAME)
            p.set_editor_property('frame',u.FrameTime(frame_number=u.FrameNumber(state['i']//2),sub_frame=(state['i']%2)*.5))
            p.set_editor_property('update_method',u.UpdatePositionMethod.JUMP)
            state['player'].set_playback_position(p);state['phase']='capture'
        else:
            points=[]
            for sword in state['swords']:
                v=u.MathLibrary.transform_location(sword.get_actor_transform(),u.Vector(96.5,0,0))
                points.append([v.x,v.y,v.z])
            state['samples'].append({'t':state['i']/48,'tips':points})
            state['i']+=1;state['phase']='seek'
            if state['i']>=500:end()
    except Exception:end(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
