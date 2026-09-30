import unreal as u
import time,json,traceback,math
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve()
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)
levels.load_level('/Game/GuansClub/FencingHall')
u.SystemLibrary.execute_console_command(editor.get_editor_world(),'t.MaxFPS 30')
levels.editor_request_begin_play()
state={'phase':'start','time':time.monotonic(),'last_frame':None,'loop_seen':False,'shots':0}
report={'samples':[]}
def xyz(v): return [v.x,v.y,v.z]
def finish(error=None):
    report['status']='failed' if error else 'passed'
    if error: report['error']=error
    report['loop_seen']=state['loop_seen']
    (ROOT/'duel_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('DUEL_VALIDATION_COMPLETE '+json.dumps(report))
    u.unregister_slate_post_tick_callback(handle)
    levels.editor_request_end_play()
    u.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
    try:
        elapsed=time.monotonic()-state['time']
        if state['phase']=='start':
            if elapsed<8:return
            world=editor.get_game_world()
            assert world,'No PIE world'
            fs=[a for a in u.GameplayStatics.get_all_actors_of_class(world,u.SkeletalMeshActor) if 'GuansDuel' in [str(t) for t in a.tags]]
            assert len(fs)==2,f'Expected 2 fencers, found {len(fs)}'
            fs.sort(key=lambda a:a.get_actor_label())
            replays=[a for a in u.GameplayStatics.get_all_actors_of_class(world,u.LevelSequenceActor) if 'GuansDuel' in [str(t) for t in a.tags]]
            assert len(replays)==1
            player=replays[0].get_editor_property('sequence_player')
            assert player.is_playing(),'Sequence not auto-playing'
            pawn=u.GameplayStatics.get_player_character(world,0)
            pc=u.GameplayStatics.get_player_controller(world,0)
            pawn.set_actor_location(u.Vector(-100,-320,100),False,True)
            pc.set_control_rotation(u.Rotator(pitch=0,yaw=90,roll=0))
            state.update(phase='sample',time=time.monotonic(),fs=fs,player=player,last_sample=-1)
            report['actors']=[a.get_actor_label() for a in fs]
        elif state['phase']=='sample':
            player=state['player']
            frame=player.get_current_time().time.frame_number.value
            if state['last_frame'] is not None and frame<state['last_frame']-20:state['loop_seen']=True
            state['last_frame']=frame
            if elapsed-state['last_sample']>1:
                sample={'frame':frame,'wall_seconds':elapsed,'fencers':[]}
                for a in state['fs']:
                    c=a.skeletal_mesh_component
                    hip=c.get_socket_location('hips_JNT')
                    head=c.get_socket_location('head_JNT')
                    sample['fencers'].append({'hips':xyz(hip),'head':xyz(head),'left_hand':xyz(c.get_socket_location('l_hand_JNT')),'right_hand':xyz(c.get_socket_location('r_hand_JNT'))})
                    assert -710<hip.x<710,f'Fencer outside piste length: {hip}'
                    assert abs(hip.y-310)<15,f'Fencer not aligned with piste 1: {hip}'
                    assert 20<hip.z<150,f'Unexpected vertical scale/placement: {hip}'
                report['samples'].append(sample)
                state['last_sample']=elapsed
            if state['shots']==0 and elapsed>3:
                u.AutomationLibrary.take_high_res_screenshot(1440,900,str(ROOT/'duel_preview_01.png'))
                state['shots']=1
            elif state['shots']==1 and elapsed>8:
                u.AutomationLibrary.take_high_res_screenshot(1440,900,str(ROOT/'duel_preview_02.png'))
                state['shots']=2
            if elapsed>16:
                assert state['loop_seen'],'Sequence did not loop'
                for i in range(2):
                    poses=[s['fencers'][i]['hips'] for s in report['samples']]
                    assert max(v[0] for v in poses)-min(v[0] for v in poses)>30,'Fencer not animating'
                report['screenshots']=[(ROOT/f'duel_preview_{i:02}.png').exists() for i in [1,2]]
                finish()
    except Exception:finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
